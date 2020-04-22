from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

database_path = 'sqlite:///nimblebuy.db'

db = SQLAlchemy()


# Init for main app
def db_init(app):
    app.config.from_object('config')
    db.app = app
    db.init_app(app)
    migrate = Migrate(app, db)
    return db


# Init for Test Suite
def setup_db(app, database_path):
    '''binds a flask application and a SQLAlchemy service'''
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)
    db.create_all()


def db_drop_and_create_all():
    '''drops the database tables and starts fresh
    can be used to initialize a clean database
    '''
    db.drop_all()
    db.create_all()


class Vegetable(db.Model):
    __tablename__ = 'vegetables'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    k_name = db.Column(db.String)
    price = db.Column(db.Float)
    image = db.Column(db.String(120))
    unit = db.Column(db.String)
    onSale = db.Column(db.Boolean, default=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    order_details = db.relationship('OrderDetails', backref='ordered_item')

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
            'id': self.id,
            'name': self.name,
            'k_name': self.k_name,
            'price': self.price,
            'image': self.image,
            'unit': self.unit,
            'onSale': self.onSale,
            'category': Category.query.get(self.category_id).format()['name']
        }

    def format2(self):
        return({
            self.id: {
                'name': self.name,
                'price': self.price,
                'image': self.image,
                'onSale': self.onSale
            }
        })

    def __repr__(self):
        return f'<Vegetable {self.id} {self.name}>'


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String)
    email_confirmed_at = db.Column(db.DateTime())
    phone = db.Column(db.String)
    fname = db.Column(db.String)
    apt = db.Column(db.String)
    apt_id = db.Column(db.Integer, db.ForeignKey('apartment.id'))
    active = db.Column('is_active', db.Boolean(), server_default='1')

    orders = db.relationship('Order', backref='customer')
    roles = db.relationship('Role', secondary='user_roles')

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'fname': self.fname,
            'apt': self.apt,
            'apt_id': self.apt_id
        }

    def __repr__(self):
        return f'<User {self.id} {self.fname}>'


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(),
                        db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(),
                        db.ForeignKey('roles.id', ondelete='CASCADE'))


class Apartment(db.Model):
    __tablename__ = 'apartment'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    resident = db.relationship('User', backref='apartment')

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def format(self):
        return {
            'id': self.id,
            'apt_name': self.name
        }


class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.Integer, primary_key=True)
    in_stock = db.Column(db.Boolean, default=True)
    stock = db.Column(db.Float)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f'<Stock {self.id} {self.stock}>'


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer,
                            db.ForeignKey('users.id'), nullable=False)
    order_number = db.Column(db.String)
    order_date = db.Column(db.String)
    order_total = db.Column(db.String)
    customer_loc = db.Column(db.String)

    order_details = db.relationship('OrderDetails', backref='order')

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def format(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'order_number': self.order_number,
            'order_date': self.order_date,
            'customer_loc': self.customer_loc,
            'order_total': self.order_total
        }

    def __repr__(self):
        return f'<Order {self.id} {self.customer_id}>'


class OrderDetails(db.Model):
    __tablename__ = 'order_details'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('vegetables.id'))
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    price = db.Column(db.String)
    qty = db.Column(db.String)
    total = db.Column(db.String)

    def format(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'order_id': self.order_id,
            'price': self.price,
            'qty': self.qty,
            'total': self.total
        }

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return f'<OrderDetails {self.id} {self.price}>'


class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    id = db.Column(db.Integer, primary_key=True)
    testimonial = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def format(self):
        return({
            'name': self.name,
            'testimonial': self.testimonial,
        })


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    vegetable = db.relationship('Vegetable', backref='category')

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def format(self):
        return({
            'name': self.name,
        })


class Enquiry(db.Model):
    __tablename__ = 'enquiries'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    locality = db.Column(db.String, nullable=False)
    enquiry = db.Column(db.String)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def format(self):
        return({
            'name': self.name,
            'phone': self.phone,
            'locality': self.locality,
            'enquiry': self.enquiry
        })
