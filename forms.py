from flask_wtf import Form
from wtforms import StringField, SelectField, SelectMultipleField, DateTimeField
from wtforms.validators import DataRequired, AnyOf, URL
from model import Apartment, db

class UserForm(Form):
    fname = StringField('fname', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    phone = StringField('phone', validators=[DataRequired()])
    apt_name = SelectMultipleField(
        'apt_name',
        validators=[DataRequired()],
        choices=[item.form() for item in Apartment.query.all()])
    apt_number = StringField('apt_number', validators=[DataRequired()])
    