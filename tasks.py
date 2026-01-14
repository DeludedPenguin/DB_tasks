import csv
from io import StringIO
from flask import Flask, render_template, request, redirect, url_for, make_response
from models import db, Task, Timer, Project
from datetime import datetime, timezone

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

@app.route('/')
def home():
    tasks = Task.query.filter_by(completed=False)\
                     .order_by((Task.due_date == None), Task.due_date, Task.priority.desc())\
                     .all()
    projects = Project.query.all()  # For the dropdown
    return render_template('index.html', 
                         title="My Task Manager", 
                         tasks=tasks,
                         projects=projects)

@app.route('/add', methods=['POST'])
def add_task():
    from datetime import datetime
    
    task_name = request.form['task']
    do_date = request.form['do_date'] if request.form['do_date'] else None
    due_date = request.form['due_date'] if request.form['due_date'] else None
    priority = int(request.form['priority']) if request.form['priority'] else 0
    project_id = int(request.form['project_id']) if request.form['project_id'] else None
    
    # Convert string dates to date objects
    if do_date:
        do_date = datetime.strptime(do_date, '%Y-%m-%d').date()
    if due_date:
        due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
    
    new_task = Task(name=task_name, do_date=do_date, due_date=due_date, priority=priority, project_id=project_id)
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

@app.route('/export/active')
def export_active_csv():
    # Get all active tasks
    tasks = Task.query.filter_by(completed=False)\
                     .order_by((Task.due_date == None), Task.due_date, Task.priority.desc())\
                     .all()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Name', 'Priority', 'Do Date', 'Due Date', 'Created At'])
    
    # Write task data
    for task in tasks:
        writer.writerow([
            task.name,
            task.priority_text,
            task.do_date.strftime('%Y-%m-%d') if task.do_date else '',
            task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
            task.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=active_tasks.csv'
    
    return response

@app.route('/export/completed')
def export_completed_csv():
    # Get all completed tasks
    tasks = Task.query.filter_by(completed=True)\
                     .order_by(Task.created_at.desc())\
                     .all()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Name', 'Priority', 'Do Date', 'Due Date', 'Created At', 'Completed'])
    
    # Write task data
    for task in tasks:
        writer.writerow([
            task.name,
            task.priority_text,
            task.do_date.strftime('%Y-%m-%d') if task.do_date else '',
            task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
            task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Yes'  # All these tasks are completed
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=completed_tasks.csv'
    
    return response

@app.route('/timer')
def timer():
    return render_template('timer.html', title="Focus Timer")

@app.route('/timer/start', methods=['POST'])
def start_timer():
    from datetime import datetime
    
    planned_minutes = int(request.form['duration'])
    
    # Create new timer session
    timer = Timer(
        start_time=datetime.now(timezone.utc),
        planned_minutes=planned_minutes,
        date=datetime.now(timezone.utc).date()
    )
    db.session.add(timer)
    db.session.commit()
    
    return redirect(url_for('timer_active', timer_id=timer.id))

@app.route('/timer/<int:timer_id>')
def timer_active(timer_id):
    timer = Timer.query.get_or_404(timer_id)
    return render_template('timer_active.html', timer=timer, title="Timer Running")

@app.route('/timer/<int:timer_id>/complete', methods=['POST'])
def complete_timer(timer_id):
    timer = Timer.query.get_or_404(timer_id)
    timer.end_time = datetime.now(timezone.utc)
    
    # Calculate actual duration in minutes - make sure both datetimes are timezone-aware
    if timer.start_time.tzinfo is None:
        # If start_time is naive, make it UTC
        start_time_aware = timer.start_time.replace(tzinfo=timezone.utc)
    else:
        start_time_aware = timer.start_time
    
    duration = timer.end_time - start_time_aware
    timer.duration_minutes = int(duration.total_seconds() / 60)
    
    timer.notes = request.form.get('notes', '')
    db.session.commit()
    
    return redirect(url_for('timer_log'))

@app.route('/timer/log')
def timer_log():
    # Show recent timer sessions
    timers = Timer.query.filter(Timer.end_time != None)\
                       .order_by(Timer.start_time.desc())\
                       .limit(20).all()
    return render_template('timer_log.html', timers=timers, title="Focus Sessions")

@app.route('/export/timers')
def export_timers_csv():
    # Get all completed timer sessions
    timers = Timer.query.filter(Timer.end_time != None)\
                       .order_by(Timer.start_time.desc())\
                       .all()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Start Time', 'End Time', 'Planned Minutes', 'Actual Minutes', 'Notes'])
    
    # Write timer data
    for timer in timers:
        writer.writerow([
            timer.date.strftime('%Y-%m-%d'),
            timer.start_time.strftime('%H:%M:%S'),
            timer.end_time.strftime('%H:%M:%S') if timer.end_time else '',
            timer.planned_minutes,
            timer.duration_minutes or '',
            timer.notes or ''
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=focus_sessions.csv'
    
    return response

@app.route('/projects')
def projects():
    projects = Project.query.all()
    return render_template('projects.html', projects=projects, title="Projects")

@app.route('/projects/new', methods=['GET', 'POST'])
def new_project():
    if request.method == 'POST':
        name = request.form['name']
        color = request.form.get('color', '#00cc33')
        
        project = Project(name=name, color=color)
        db.session.add(project)
        db.session.commit()
        
        return redirect(url_for('projects'))
    
    return render_template('new_project.html', title="New Project")

@app.route('/projects/<int:project_id>')
def project_tasks(project_id):
    project = Project.query.get_or_404(project_id)
    tasks = Task.query.filter_by(project_id=project_id, completed=False)\
                     .order_by((Task.due_date == None), Task.due_date, Task.priority.desc())\
                     .all()
    return render_template('project_tasks.html', project=project, tasks=tasks, title=f"{project.name} Tasks")

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5001)