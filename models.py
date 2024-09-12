from extensions import db

class Applicant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    essay1 = db.Column(db.Text, nullable=False)
    essay2 = db.Column(db.Text, nullable=False)
    essay3 = db.Column(db.Text, nullable=False)
    essay1_score = db.Column(db.Integer)
    essay2_score = db.Column(db.Integer)
    essay3_score = db.Column(db.Integer)
    essay1_feedback = db.Column(db.Text)
    essay2_feedback = db.Column(db.Text)
    essay3_feedback = db.Column(db.Text)

    def __repr__(self):
        return f'<Applicant {self.name}>'

class EssayQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<EssayQuestion {self.id}>'
