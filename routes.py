from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from models import db, Applicant
from forms import ApplicationForm
from sqlalchemy.exc import SQLAlchemyError

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/apply', methods=['GET', 'POST'])
def apply():
    form = ApplicationForm()
    existing_applicant = None

    if request.method == 'GET' and request.args.get('email'):
        email = request.args.get('email')
        current_app.logger.debug(f"Checking for existing applicant with email: {email}")
        existing_applicant = Applicant.query.filter_by(email=email).first()
        if existing_applicant:
            current_app.logger.debug(f"Existing applicant found: {existing_applicant}")
            form = ApplicationForm(obj=existing_applicant)
        else:
            current_app.logger.debug("No existing applicant found")

    if form.validate_on_submit():
        current_app.logger.debug("Form validated successfully")
        try:
            existing_applicant = Applicant.query.filter_by(email=form.email.data).first()
            if existing_applicant:
                current_app.logger.debug(f"Updating existing applicant: {existing_applicant}")
                form.populate_obj(existing_applicant)
            else:
                current_app.logger.debug("Creating new applicant")
                new_applicant = Applicant(
                    name=form.name.data,
                    email=form.email.data,
                    essay1=form.essay1.data,
                    essay2=form.essay2.data,
                    essay3=form.essay3.data
                )
                db.session.add(new_applicant)

            db.session.commit()
            current_app.logger.info('Application submitted successfully')
            flash('Your application has been submitted successfully!', 'success')
            return redirect(url_for('main.confirmation'))
        except SQLAlchemyError as e:
            current_app.logger.error(f'Database error occurred during form submission: {str(e)}')
            db.session.rollback()
            flash('A database error occurred. Please try again.', 'error')
        except Exception as e:
            current_app.logger.error(f'Unexpected error occurred during form submission: {str(e)}')
            db.session.rollback()
            flash('An unexpected error occurred. Please try again.', 'error')
    else:
        current_app.logger.info('Form validation failed')
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", 'error')
    
    current_app.logger.info('Rendering application.html template')
    return render_template('application.html', form=form, existing_applicant=existing_applicant)

@main.route('/confirmation')
def confirmation():
    current_app.logger.info('Entering confirmation route')
    return render_template('confirmation.html')
