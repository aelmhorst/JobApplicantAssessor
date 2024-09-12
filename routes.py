from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, session
from models import db, Applicant
from forms import ApplicationForm, LoginForm
from sqlalchemy.exc import SQLAlchemyError
from ai_scoring import evaluate_essay, parse_ai_response
from functools import wraps

main = Blueprint('main', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

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
            
            # AI Scoring
            essay_prompts = [
                "Describe a challenging situation you've faced in your professional life and how you overcame it.",
                "What are your career goals for the next five years, and how does this position align with them?",
                "Describe a time when you had to learn a new skill quickly. How did you approach the learning process?"
            ]
            essay_scores = []
            essay_feedbacks = []
            
            for i, essay in enumerate([form.essay1.data, form.essay2.data, form.essay3.data], start=1):
                ai_response = evaluate_essay(essay, essay_prompts[i-1])
                score, feedback = parse_ai_response(ai_response)
                essay_scores.append(score or 0)  # Use 0 if score is None
                essay_feedbacks.append(feedback or 'No feedback available')  # Use a default message if feedback is None

            if existing_applicant:
                current_app.logger.debug(f"Updating existing applicant: {existing_applicant}")
                form.populate_obj(existing_applicant)
                existing_applicant.essay1_score = essay_scores[0]
                existing_applicant.essay2_score = essay_scores[1]
                existing_applicant.essay3_score = essay_scores[2]
                existing_applicant.essay1_feedback = essay_feedbacks[0]
                existing_applicant.essay2_feedback = essay_feedbacks[1]
                existing_applicant.essay3_feedback = essay_feedbacks[2]
            else:
                current_app.logger.debug("Creating new applicant")
                new_applicant = Applicant(
                    name=form.name.data,
                    email=form.email.data,
                    essay1=form.essay1.data,
                    essay2=form.essay2.data,
                    essay3=form.essay3.data,
                    essay1_score=essay_scores[0],
                    essay2_score=essay_scores[1],
                    essay3_score=essay_scores[2],
                    essay1_feedback=essay_feedbacks[0],
                    essay2_feedback=essay_feedbacks[1],
                    essay3_feedback=essay_feedbacks[2]
                )
                db.session.add(new_applicant)

            db.session.commit()
            current_app.logger.info('Application submitted and scored successfully')
            flash('Your application has been submitted and evaluated successfully!', 'success')
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

@main.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == 'admin' and form.password.data == 'password':
            session['admin'] = True
            flash('You have been logged in.', 'success')
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('admin_login.html', form=form)

@main.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))

@main.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    applicants = Applicant.query.all()
    return render_template('admin_dashboard.html', applicants=applicants)

@main.route('/admin/applicant/<int:id>')
@admin_required
def admin_applicant_detail(id):
    applicant = Applicant.query.get_or_404(id)
    return render_template('admin_applicant_detail.html', applicant=applicant)
