from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length
from email_validator import validate_email, EmailNotValidError

class ApplicationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(message='Invalid email address'), Length(max=120)])
    essay1 = TextAreaField('Essay 1', validators=[DataRequired(), Length(min=100, max=10000)])
    essay2 = TextAreaField('Essay 2', validators=[DataRequired(), Length(min=100, max=10000)])
    essay3 = TextAreaField('Essay 3', validators=[DataRequired(), Length(min=100, max=10000)])

    def validate_email(self, field):
        try:
            validate_email(field.data)
        except EmailNotValidError as e:
            raise ValidationError(str(e))

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])

class EssayQuestionForm(FlaskForm):
    question_text = TextAreaField('Question Text', validators=[DataRequired(), Length(max=500)])
    is_active = BooleanField('Active')
