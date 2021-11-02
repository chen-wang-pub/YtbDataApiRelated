from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, URL
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')


    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class DownloadRequestForm(FlaskForm):
    ytbvideo = StringField('Youtube Video Link', validators=[URL()])
    ytblist = StringField('Youtube Playlist Link', validators=[URL()])
    spotifylist = StringField('Spotify Playlist Link', validators=[URL()])

    def validate(self, extra_validators=None):
        # https://stackoverflow.com/questions/64222815/flask-wtforms-validation-inputrequired-for-at-least-one-field
        if super().validate(extra_validators):
            if not self.ytbvideo.data and not self.ytblist.data and not self.spotifylist.data:
                self.ytbvideo.errors.append("At least one of the field should not be empty.")
                return False
            else:
                return True
        return False