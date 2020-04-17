from functools import wraps
import json
from os import environ as env
from werkzeug.exceptions import HTTPException
from flask_cors import CORS, cross_origin

from dotenv import load_dotenv, find_dotenv
from flask import Flask, jsonify, redirect
from flask import render_template, session
from flask import url_for, request, flash
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode
from models import db_init, Vegetable, User, Order
from models import OrderDetails, Apartment, Category
from models import Stock, Testimonial, Role, UserRoles
from models import Enquiry
from flask_migrate import Migrate
from flask_babelex import Babel
from auth import AuthError, requires_auth, store_permissions
from shortid import ShortId
import maya
import data
import constants

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

AUTH0_CALLBACK_URL = env.get(constants.AUTH0_CALLBACK_URL)
AUTH0_CLIENT_ID = env.get(constants.AUTH0_CLIENT_ID)
AUTH0_CLIENT_SECRET = env.get(constants.AUTH0_CLIENT_SECRET)
AUTH0_DOMAIN = env.get(constants.AUTH0_DOMAIN)
AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN
AUTH0_AUDIENCE = env.get(constants.AUTH0_AUDIENCE)

app = Flask(__name__, static_url_path='/public', static_folder='./public')
app.secret_key = constants.SECRET_KEY
app.debug = True
db = db_init(app)
babel = Babel(app)
CORS(app)
sid = ShortId()

@app.errorhandler(Exception)
def handle_auth_error(ex):
    response = jsonify(message=str(ex))
    response.status_code = (ex.code if isinstance(ex, HTTPException) else 500)
    return response

oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    api_base_url=AUTH0_BASE_URL,
    access_token_url=AUTH0_BASE_URL + '/oauth/token',
    authorize_url=AUTH0_BASE_URL + '/authorize',
    client_kwargs={
        'scope': 'openid profile email',
    },
)

def mergeDicts(dict1, dict2):
    if isinstance(dict1, list) and isinstance(dict2, list):
        return dict1 + dict2
    elif isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items())+ list(dict2.items))

# Basic Page Routes --------------------------------------------------------------------
# Home Route
@app.route('/')
def home():
    response = [item.format() for item in Vegetable.query.all()]
    categories = [item.format() for item in Category.query.all()]
    return render_template('home.html', data=response, categories=categories)

# Home Route Categorized
@app.route('/category/<string:category>')
def get_category(category):
    try:
        category = Category.query.filter_by(name=category).first()
        response = [item.format() for item in Vegetable.query.filter_by(category=category).all()]
        categories = [item.format() for item in Category.query.all()]
        return render_template('home.html', data=response, categories=categories)

    except Exception:
        flash('Error fetching category')
        return redirect(request.referrer)

# About Page
@app.route('/about')
def about_page():
    testimonials = [item.format() for item in Testimonial.query.all()]
    return render_template('about.html', testimonials=testimonials)
# -----------------------------------------------------------------------------------------

# Auth0 Routes ------------------------------------------------------------------------------
# Login Route
@app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri=AUTH0_CALLBACK_URL, audience=AUTH0_AUDIENCE)

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    params = {'returnTo': url_for('home', _external=True), 'client_id': AUTH0_CLIENT_ID}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))

# Login Callback Route
@app.route('/callback')
def callback_handling():
    token = auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    session['token'] = token.get('access_token')
    session['permissions'] = store_permissions()

    session[constants.JWT_PAYLOAD] = userinfo
    session[constants.PROFILE_KEY] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture'],
        'email':userinfo['email']
    }

    try:
        if db.session.query(User.id).filter_by(email=userinfo['email']).scalar() is None:
            user = User(fname=userinfo['name'], email=userinfo['email'])
            user.insert()
    except Exception:
        flash('Something went wrong')

    return redirect('/')
# ----------------------------------------------------------------------------------------

# User Profile Routes---------------------------------------------------------------------
# GET User Profile Page
@app.route('/profile')
def user_profile():
    if 'profile' not in session:
        return redirect(url_for('about_page'))
    user = User.query.filter_by(email=session.get(constants.PROFILE_KEY)['email']).first()
    apt = [apt.format() for apt in Apartment.query.all()]
    return render_template('profile.html', apt=apt, user = user.format())

# PATCH User Profile data
@app.route('/profile/update', methods=['POST'])
def update_profile():
    form_data = request.form.to_dict()
    print(form_data)
    if form_data['apt_name'] == 'Select Apartment Name':
        flash('Please select apartment name to proceed')
    try:
        user = User.query.filter_by(email=session.get(constants.PROFILE_KEY)['email']).first()
        apt = Apartment.query.filter_by(name=form_data['apt_name']).first()
        user.fname = form_data['name']
        user.phone = form_data['phone']
        user.apartment = apt
        user.apt = form_data['apt_number']
        user.update()
        flash('Profile updated successfully')
    except Exception as e:
        print(f'Error ==> {e}')
        flash('Something went wrong')
        return redirect(request.referrer)

    return redirect(request.referrer)
# --------------------------------------------------------------------------------------------

# Shopping Cart Routes ---------------------------------------------------------------------
# GET Cart Page
@app.route('/cart')
def cart():
    try:
        if 'profile' not in session:
            return redirect(url_for('about_page'))
        if 'cart' in session and len(session['cart']) > 0:
            user = User.query.filter_by(email=session.get(constants.PROFILE_KEY)['email']).first()
            if user.apartment is None:
                flash("Please update your personal details in Account Settings first. Thank You")
                return redirect(request.referrer)
            apt_name = user.apartment.format()
            subtotal = get_cart_total()
            shipping = 10
            subtotal += shipping
            return render_template('cart.html', subtotal=subtotal,
                shipping=shipping, user = user.format(), apt_name=apt_name)
        else: 
            flash('Please add something to the cart first!')
            return redirect(request.referrer)
    except Exception as e:
        print(f'Error ==> {e}')
        return redirect(request.referrer)


# Add Item to Cart
@app.route('/cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'profile' in session:
        try:
            veg = Vegetable.query.get(product_id).format()
            veg['qty'] = 1
            new_item = [veg]
            if 'cart' in session:
                if not any(item['id'] == product_id for item in session['cart']):
                    session['cart'] = mergeDicts(session['cart'], new_item)
                else:
                    flash(veg['name'].capitalize() + ' already in cart!')
                return redirect(request.referrer)        
            else:
                session['cart'] = new_item
                return redirect(request.referrer)
        except Exception as e:
            print(f'Error ==> {e}')
        finally:
            return redirect(request.referrer)
    else:
        flash('Please Login to add items to cart! :)')
        return redirect(request.referrer)

# DELETE Cart Item
@app.route('/cart/delete/<int:product_id>', methods=['POST'])
def delete_item_in_cart(product_id):
    if 'user' not in session and 'cart' not in session and len(session['cart'] <=0):
        return redirect(url_for('home'))
    try:
        session.modified = True
        arr = session['cart']
        arr[:] = [d for d in arr if d.get('id') != product_id]
        session['cart'] = arr
        if len(session['cart']) == 0 :
            flash('All items removed from cart')
            return redirect(url_for('home'))
        return redirect(url_for('cart'))

    except Exception as e:
        return redirect(url_for('cart'))
        print(f'Error ==> {e}')

# UPDATE Cart Item
@app.route('/cart/update/<int:product_id>')
def update_cart(product_id):
    if 'cart' not in session and len(session['cart']) <= 0:
        return redirect(url_for('cart'))
    else:
        qty = request.args.get('qty')
        try:
            session.modified = True
            for item in session['cart']:
                if item['id'] == product_id:
                    item['qty'] = qty
                    flash('Item was updated')
                    return redirect(url_for('cart'))
        except Exception as e:
            flash('Something went wrong. Please try again.')
            print(f'Error ==> {e}')
            return redirect(url_for('cart'))

# Calculate total order cost
def get_cart_total():
    subtotal = 0
    for product in session['cart']:
        subtotal += float(product['price']) * float(product['qty'])
    return subtotal
# --------------------------------------------------------------------------

# Order Creation Routes -----------------------------------------------------------
# POST Create the order
@app.route('/create-order', methods=['POST'])
def create_order():
    try:
        shipping = 10
        subtotal = get_cart_total() + shipping
        session['subtotal'] = subtotal
        customer = User.query.filter_by(email=session.get(constants.PROFILE_KEY)['email']).first()
        order = Order(customer=customer, order_number=sid.generate(), order_date=str(maya.now()), order_total=subtotal)
        order.insert()
        session['order'] = order.format()
        for product in session['cart']:
            ordered_item = Vegetable.query.get(int(product['id']))
            order_details = OrderDetails(ordered_item=ordered_item, order=order, price=product['price'], qty=product['qty'], total=subtotal)
            order_details.insert()
        session.pop('cart', None)
        return redirect(url_for('order_confirm'))

    except Exception as e:
        print(f'Error ==> {e}')
        flash('Something went wrong')
        return redirect(request.referrer)

# Confirm Order Route
@app.route('/confirm')
def order_confirm():
    return render_template('confirmation.html')
# -------------------------------------------------------------------------------

# Enquiries
@app.route('/enquire', methods=['POST'])
def submit_enquiry():
    data = request.form.to_dict()
    try:
        enquiry = Enquiry(name=data['name'], phone=data['phone'], locality=data['locality'])
        enquiry.insert()
        flash('Your details were submitted. We will get back to you very shortly.')
        return redirect(request.referrer)
    except Exception:
        flash('Your enquiry could not be submitted. Please try again later')
        return redirect(request.referrer)

# ADMIN Routes -------------------------------------------------------------------------------
# GET Admin page
@app.route('/admin_page')
@requires_auth('get:admin_dashboard')
def get_admin_page(jwt):
    return render_template('admin.html')

# Debug Route
@app.route('/session')
def get_session():
    return jsonify({
        'jwt': session.get('jwt_payload'),
        'profile': session.get(constants.PROFILE_KEY),
        'cart': session.get('cart'),
        'token':session.get('token'),
        'permissions': session.get('permissions')
    })

# Init DB Data
def import_db():
    import data
    from models import Vegetable, Apartment, Category, Testimonial
    for item in data.apartments:
        apt = Apartment(id=item['id'], name=item['name'])
        apt.insert()
    for item in data.categories:
        cat = Category(id=item['id'], name=item['name'])
        cat.insert()
    for item in data.testimonials:
        test = Testimonial(id=item['id'], name=item['name'], testimonial=item['testimonial'])
        test.insert()
    for item in data.products:
        veg = Vegetable(category_id=item['category_id'], image=item['image'],
                        k_name=item['k_name'], name=item['name'],
                        onSale=bool(item['onSale']), price=item['price'],
                        unit=item['unit'])
        veg.insert()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=env.get('PORT', 3000))
