import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from models import setup_test_db, Order, User, db_init
import random
import math
import string
import maya
from app import app

load_dotenv()


class NimbleTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = app
        self.client = self.app.test_client
        self.database_name = "nimblebuy_test"
        self.database_path = "sqlite:///{}".format(self.database_name)
        # setup_test_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
        
        with self.app.test_client() as self.c:
            with self.c.session_transaction() as self.sess:
                self.sess['profile'] = 'user'
                self.sess['cart'] = [{
                    "category": "vegetable",
                    "id": 1,
                    "image": "carrot",
                    "k_name": "ಕ್ಯಾರೆಟ್",
                    "name": "carrot",
                    "onSale": True,
                    "price": 60,
                    "qty": 1,
                    "unit": "kg"
                    },
                    {
                    "category": "vegetable",
                    "id": 2,
                    "image": "beans",
                    "k_name": "ಬೀನ್ಸ್",
                    "name": "beans",
                    "onSale": True,
                    "price": 120,
                    "qty": 1,
                    "unit": "kg"
                    }
                    ]

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
        self.assertEqual(res.status_code, 200)

    def test_get_cart_page(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess['cart'] = 'value'
                sess['profile'] = 'profile'
        res = self.client().get('/cart')
        self.assertEqual(res.status_code, 200)
    

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
