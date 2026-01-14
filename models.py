from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    do_date = db.Column(db.Date, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.Integer, default=0)  # 0=none, 1=low, 2=medium, 3=high
    
    def __repr__(self):
        return f'<Task {self.name}>'
    
    @property
    def priority_text(self):
        priority_map = {0: "", 1: "Low", 2: "Medium", 3: "High"}
        return priority_map.get(self.priority, "")
    
    @property 
    def priority_color(self):
        color_map = {0: "", 1: "#28a745", 2: "#ffc107", 3: "#dc3545"}
        return color_map.get(self.priority, "")