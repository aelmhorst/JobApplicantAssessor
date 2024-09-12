from extensions import db

class Applicant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    essay1 = db.Column(db.Text, nullable=False)
    essay2 = db.Column(db.Text, nullable=False)
    essay3 = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Applicant {self.name}>'
