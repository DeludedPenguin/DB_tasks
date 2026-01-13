from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    do_date = db.Column(db.Date, nullable=True)  # When you plan to work on it
    due_date = db.Column(db.Date, nullable=True)  # When it must be finished
    
    def __repr__(self):
        return f'<Task {self.name}>'