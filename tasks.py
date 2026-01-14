from flask import Flask, render_template, request, redirect, url_for
from models import db, Task

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

@app.route('/')
def home():
    # Only show incomplete tasks
    tasks = Task.query.filter_by(completed=False)\
                     .order_by((Task.due_date == None), Task.due_date, Task.priority.desc())\
                     .all()
    return render_template('index.html', 
                         title="My Task Manager", 
                         tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    from datetime import datetime
    
    task_name = request.form['task']
    do_date = request.form['do_date'] if request.form['do_date'] else None
    due_date = request.form['due_date'] if request.form['due_date'] else None
    priority = int(request.form['priority']) if request.form['priority'] else 0

    
    # Convert string dates to date objects
    if do_date:
        do_date = datetime.strptime(do_date, '%Y-%m-%d').date()
    if due_date:
        due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
    
    new_task = Task(name=task_name, do_date=do_date, due_date=due_date, priority=priority)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/complete/<int:task_id>')
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = True
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete/<int:task_id>')
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/completed')
def completed_tasks():
    # Show completed tasks, most recent first
    tasks = Task.query.filter_by(completed=True)\
                     .order_by(Task.created_at.desc())\
                     .all()
    return render_template('completed.html', 
                         title="Completed Tasks", 
                         tasks=tasks)

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)