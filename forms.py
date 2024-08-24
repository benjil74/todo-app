from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateField
from wtforms.validators import DataRequired, URL


class ToDoForm(FlaskForm):
    to_do = StringField('Write your next task:', validators=[DataRequired()])
    date_to_do = DateField('Date:', format='%Y-%m-%d')
    submit = SubmitField('Submit')


class NewToDoForm(FlaskForm):
    list_name = StringField('Name of your list:', validators=[DataRequired()])
    to_do = StringField('Write your first task:', validators=[DataRequired()])
    date_to_do = DateField('Date:', format='%Y-%m-%d')
    submit = SubmitField('Submit')


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")