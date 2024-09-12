from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, session, send_file
from models import db, Applicant, EssayQuestion
from forms import ApplicationForm, LoginForm, SearchForm, EssayQuestionForm
from sqlalchemy.exc import SQLAlchemyError
from ai_scoring import evaluate_essay, parse_ai_response
from functools import wraps
import csv
import io

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
        existing_applicant = Applicant.query.filter_by(email=email).first()
        if existing_applicant:
            form = ApplicationForm(obj=existing_applicant)

    active_questions = EssayQuestion.query.filter_by(is_active=True).order_by(EssayQuestion.id).limit(3).all()

    if form.validate_on_submit():
        try:
            existing_applicant = Applicant.query.filter_by(email=form.email.data).first()
            
            # AI Scoring
            essay_scores = []
            essay_feedbacks = []
            
            for i, essay in enumerate([form.essay1.data, form.essay2.data, form.essay3.data], start=1):
                question = active_questions[i-1] if i <= len(active_questions) else None
                prompt = question.question_text if question else f"Essay {i}"
                ai_response = evaluate_essay(essay, prompt)
                score, feedback = parse_ai_response(ai_response)
                essay_scores.append(score or 0)
                essay_feedbacks.append(feedback or 'No feedback available')

            if existing_applicant:
                form.populate_obj(existing_applicant)
                existing_applicant.essay1_score = essay_scores[0]
                existing_applicant.essay2_score = essay_scores[1]
                existing_applicant.essay3_score = essay_scores[2]
                existing_applicant.essay1_feedback = essay_feedbacks[0]
                existing_applicant.essay2_feedback = essay_feedbacks[1]
                existing_applicant.essay3_feedback = essay_feedbacks[2]
            else:
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
            flash('Your application has been submitted and evaluated successfully!', 'success')
            return redirect(url_for('main.confirmation'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('A database error occurred. Please try again.', 'error')
        except Exception as e:
            db.session.rollback()
            flash('An unexpected error occurred. Please try again.', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", 'error')
    
    return render_template('application.html', form=form, existing_applicant=existing_applicant, active_questions=active_questions)

@main.route('/confirmation')
def confirmation():
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
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search_form = SearchForm()
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')

    query = Applicant.query

    if search_query:
        query = query.filter((Applicant.name.ilike(f'%{search_query}%')) | (Applicant.email.ilike(f'%{search_query}%')))

    if sort_by == 'total_score':
        query = query.order_by(db.desc(Applicant.essay1_score + Applicant.essay2_score + Applicant.essay3_score)) if sort_order == 'desc' else query.order_by(Applicant.essay1_score + Applicant.essay2_score + Applicant.essay3_score)
    elif sort_by in ['name', 'email']:
        query = query.order_by(db.desc(getattr(Applicant, sort_by))) if sort_order == 'desc' else query.order_by(getattr(Applicant, sort_by))
    else:
        query = query.order_by(db.desc(Applicant.id)) if sort_order == 'desc' else query.order_by(Applicant.id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    applicants = pagination.items

    total_applicants = Applicant.query.count()
    average_score = db.session.query(db.func.avg(Applicant.essay1_score + Applicant.essay2_score + Applicant.essay3_score)).scalar() or 0

    return render_template('admin_dashboard.html', 
                           applicants=applicants, 
                           pagination=pagination, 
                           search_form=search_form, 
                           search_query=search_query,
                           sort_by=sort_by,
                           sort_order=sort_order,
                           total_applicants=total_applicants,
                           average_score=average_score)

@main.route('/admin/applicant/<int:id>')
@admin_required
def admin_applicant_detail(id):
    applicant = Applicant.query.get_or_404(id)
    return render_template('admin_applicant_detail.html', applicant=applicant)

@main.route('/admin/export_csv')
@admin_required
def export_csv():
    applicants = Applicant.query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Name', 'Email', 'Essay 1 Score', 'Essay 2 Score', 'Essay 3 Score', 'Total Score'])
    
    for applicant in applicants:
        total_score = (applicant.essay1_score or 0) + (applicant.essay2_score or 0) + (applicant.essay3_score or 0)
        writer.writerow([applicant.id, applicant.name, applicant.email, 
                         applicant.essay1_score, applicant.essay2_score, applicant.essay3_score, 
                         total_score])
    
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     attachment_filename='applicants.csv')

@main.route('/admin/questions', methods=['GET', 'POST'])
@admin_required
def manage_questions():
    questions = EssayQuestion.query.all()
    form = EssayQuestionForm()

    if form.validate_on_submit():
        new_question = EssayQuestion(question_text=form.question_text.data, is_active=form.is_active.data)
        db.session.add(new_question)
        db.session.commit()
        flash('New question added successfully!', 'success')
        return redirect(url_for('main.manage_questions'))

    return render_template('manage_questions.html', questions=questions, form=form)

@main.route('/admin/questions/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_question(id):
    question = EssayQuestion.query.get_or_404(id)
    form = EssayQuestionForm(obj=question)

    if form.validate_on_submit():
        question.question_text = form.question_text.data
        question.is_active = form.is_active.data
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('main.manage_questions'))

    return render_template('edit_question.html', form=form, question=question)

@main.route('/admin/questions/<int:id>/delete', methods=['POST'])
@admin_required
def delete_question(id):
    question = EssayQuestion.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('main.manage_questions'))
