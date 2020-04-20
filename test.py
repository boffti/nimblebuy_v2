import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from models import Order, User, Vegetable, OrderDetails, Category, setup_db, db_drop_and_create_all
from flask_migrate import Migrate
from flask_user import UserMixin
import random
import math
import string
import maya
from app import app, import_db

load_dotenv()


class NimbleTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = app
        app.config['SECRET_KEY'] = 'SECRET_SECRET'
        self.client = self.app.test_client
        self.database_name = "nimblebuy_test"
        self.database_path = "sqlite:///{}.db".format(self.database_name)
        # setup_db(self.app, self.database_path)
        # db_drop_and_create_all()

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            # self.db.init_app(self.app)
            # create all tables
            # self.db.create_all()
            # import_db()

        self.new_order = {
            'customer_id': 1,
            'order_number': "ABCD",
            'order_date': "ABCD",
            'order_total': 123,
            'customer_loc': 1
        }

    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_get_about_page(self):
        res = self.client().get('/about')
        self.assertEqual(res.status_code, 200)

    def test_get_cart_page(self):
        res = self.client().get('/cart')
        self.assertEqual(res.status_code, 302)

    def test_get_profile_page(self):
        with self.app.test_client() as self.c:
            with self.c.session_transaction() as self.sess:
                self.sess['profile'] = 'user'
        res = self.client().get('/profile')
        self.assertEqual(res.status_code, 302)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
