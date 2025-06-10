from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField,
    BooleanField, TextAreaField, SelectField
)
from wtforms.validators import DataRequired, Length, EqualTo, Email

class RegistrationForm(FlaskForm):
    first_name = StringField('Usuario', validators=[DataRequired(),Length(max=64)])
    ci         = StringField('Cédula', validators=[Length(max=20)])
    password   = PasswordField('Contraseña', validators=[DataRequired(), Length(min=4)])
    confirm    = PasswordField('Repite contraseña',
                   validators=[DataRequired(), EqualTo('password')])
    submit     = SubmitField('Registrarse')

class LoginForm(FlaskForm):
    ci       = StringField('Cédula', validators=[DataRequired(),Length(max=20)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recuérdame')
    submit   = SubmitField('Iniciar sesión')

class ContactForm(FlaskForm):
    name    = StringField('Tu nombre', validators=[DataRequired(),Length(max=64)])
    email   = StringField('Tu correo', validators=[DataRequired(),Email()])
    message = TextAreaField('Mensaje', validators=[DataRequired(),Length(max=500)])
    submit  = SubmitField('Enviar')

class BookForm(FlaskForm):
    title       = StringField('Título', validators=[DataRequired(),Length(max=128)])
    author      = StringField('Autor', validators=[DataRequired(),Length(max=128)])
    description = TextAreaField('Descripción', validators=[Length(max=1000)])
    category    = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    submit      = SubmitField('Guardar')
