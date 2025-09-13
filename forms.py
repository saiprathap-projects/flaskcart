from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DecimalField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo, Optional, URL

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[Email(), DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log In")

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[Email(), DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("Confirm Password", validators=[EqualTo('password', message='Passwords must match')])
    submit = SubmitField("Create Account")

class ProductForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional()])
    price = DecimalField("Price", places=2, validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField("Stock", validators=[DataRequired(), NumberRange(min=0)])
    image_url = StringField("Image URL", validators=[Optional(), URL(require_tld=False, message="Enter a valid URL")])
    submit = SubmitField("Save")
