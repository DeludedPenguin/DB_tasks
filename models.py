from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    do_date = db.Column(db.Date, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.Integer, default=0)  # 0=none, 1=low, 2=medium, 3=high
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=True)
    
    def __repr__(self):
        return f'<Task {self.name}>'
    
    @property
    def priority_text(self):
        priority_map = {0: "", 1: "low", 2: "medium", 3: "high"}
        return priority_map.get(self.priority, "")
    
    @property 
    def priority_color(self):
        color_map = {0: "", 1: "#28a745", 2: "#ffc107", 3: "#dc3545"}
        return color_map.get(self.priority, "")

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    color = db.Column(db.String(7), default="#00cc33")  # Hex color code
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to tasks
    tasks = db.relationship('Task', backref='project', lazy=True)
    
    def __repr__(self):
        return f'<Project {self.name}>'

class Timer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)  # Actual duration
    planned_minutes = db.Column(db.Integer, nullable=False)  # 10, 25, or 30
    notes = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    
    def __repr__(self):
        return f'<Timer {self.duration_minutes}min on {self.date}>'