"""Python Flask WebApp Auth0 integration example
"""
from functools import wraps
import json
from os import environ as env
from werkzeug.exceptions import HTTPException

from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import session
from flask import url_for, request, flash
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode
from models import db_init, Vegetable, User, Order, OrderDetails, Apartment, Category, Stock, Testimonial, Role, UserRoles
from flask_migrate import Migrate
from flask_babelex import Babel

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


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if constants.PROFILE_KEY not in session:
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated

def mergeDicts(dict1, dict2):
    if isinstance(dict1, list) and isinstance(dict2, list):
        return dict1 + dict2
    elif isinstance(dict1, dict) and isinstance(dict2, dict):
        return dict(list(dict1.items())+ list(dict2.items))

# Controllers API
@app.route('/')
def home():
    response = [item.format() for item in Vegetable.query.all()]
    categories = [item.format() for item in Category.query.all()]
    return render_template('home.html', data=response, categories=categories)

@app.route('/category/<string:category>')
def get_category(category):
    try:
        category = Category.query.filter_by(name=category).first()
        response = [item.format() for item in Vegetable.query.filter_by(category=category).all()]
        categories = [item.format() for item in Category.query.all()]
        return render_template('home.html', data=response, categories=categories)

    except:
        return 'Error'
        flash('Error fetching category')

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/cart')
def cart():
    if 'cart' in session:
        subtotal = 0
        for product in session['cart']:
            subtotal += float(product['price']) * float(product['qty'])
        return render_template('cart.html', subtotal=subtotal)
    else: 
        flash('Please add something to the cart first!')
        return redirect(request.referrer)

@app.route('/settings')
def settings():
    apt = [apt.format() for apt in Apartment.query.all()]
    return render_template('profile.html', apt=apt)

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

@app.route('/cart/delete/<int:product_id>', methods=['POST'])
def delete_item_in_cart(product_id):
    if 'user' not in session and 'cart' not in session and len(session['cart'] <=0):
        return redirect(url_for('home'))
    try:
        session.modified = True
        arr = session['cart']
        arr[:] = [d for d in arr if d.get('id') != product_id]
        session['cart'] = arr
        return redirect(url_for('cart'))

    except Exception as e:
        return redirect(url_for('cart'))
        print(f'Error ==> {e}')

@app.route('/callback')
def callback_handling():
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    session[constants.JWT_PAYLOAD] = userinfo
    session[constants.PROFILE_KEY] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture']
    }
    return redirect('/')


@app.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri=AUTH0_CALLBACK_URL, audience=AUTH0_AUDIENCE)


@app.route('/logout')
def logout():
    session.clear()
    params = {'returnTo': url_for('home', _external=True), 'client_id': AUTH0_CLIENT_ID}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))


@app.route('/dashboard')
@requires_auth
def dashboard():
    return render_template('dashboard.html',
                           userinfo=session[constants.PROFILE_KEY],
                           userinfo_pretty=json.dumps(session[constants.JWT_PAYLOAD], indent=4))

@app.route('/session')
def func_name():
    return jsonify({
        'jwt': session.get('jwt_payload'),
        'profile': session.get(constants.PROFILE_KEY),
        'cart': session.get('cart')
    })

def import_db():
    import data
    for item in data.data:
        veg = Vegetable(category_id=item['category_id'], image=item['image'], k_name=item['k_name'], name=item['name'], onSale=bool(item['onSale']), price=item['price'], unit=item['unit'])
        veg.insert()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=env.get('PORT', 3000))
