#!/usr/bin/env python3
"""
Script to import Todoist CSV export into DB_tasks database.

Usage:
1. Place this script in your task-manager folder (same directory as tasks.py)
2. Place the todoist_exp_all.csv file in the same folder
3. Make sure your Flask app is NOT running
4. Run: python import_todoist.py
"""

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the current directory to Python path so we can import our models
sys.path.append('.')

try:
    from models import db, Task, Project
    from tasks import app  # Import the Flask app
except ImportError as e:
    print(f"Error: Could not import models. Make sure you're running this from your task-manager directory.")
    print(f"Import error: {e}")
    sys.exit(1)

def parse_todoist_date(date_str):
    """Parse Todoist date formats into Python date objects"""
    if not date_str or date_str.strip() == '':
        return None
    
    # Common Todoist date formats
    formats = [
        '%d-Jan-%y',    # 14-Jan-26
        '%d-Jan',       # 14-Jan (current year assumed)
        '%Y-%m-%d',     # 2026-01-14
        '%d/%m/%Y',     # 14/01/2026
    ]
    
    date_str = date_str.strip()
    
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            # If year is missing, assume current year
            if parsed_date.year == 1900:  # strptime default
                parsed_date = parsed_date.replace(year=2026)
            return parsed_date.date()
        except ValueError:
            continue
    
    print(f"Warning: Could not parse date: '{date_str}'")
    return None

def convert_todoist_priority(todoist_priority):
    """Convert Todoist priority (1-4) to our priority (0-3)"""
    if not todoist_priority or todoist_priority == '':
        return 0
    
    # Todoist: 1=lowest, 4=highest
    # Ours: 0=none, 1=low, 2=medium, 3=high
    priority_map = {
        '1': 1,  # Low
        '2': 1,  # Low  
        '3': 2,  # Medium
        '4': 3,  # High
    }
    
    return priority_map.get(str(todoist_priority), 0)

def import_todoist_data():
    """Main import function"""
    
    csv_file = Path('todoist_exp_all.csv')
    if not csv_file.exists():
        print("Error: todoist_exp_all.csv not found in current directory")
        return
    
    with app.app_context():
        # First, let's see what projects we need
        projects_needed = set()
        
        print("Analyzing CSV file...")
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['TYPE'] == 'task' and row['PROJECT']:
                    projects_needed.add(row['PROJECT'])
        
        print(f"Found {len(projects_needed)} projects in Todoist:")
        for project in sorted(projects_needed):
            print(f"  - {project}")
        
        # Color mapping for projects (you can customize this)
        project_colors = {
            'work': '#007bff', 'engagement': '#28a745', 'personal': '#6f42c1',
            'to-read': '#ffc107', 'CELGAI': '#dc3545', 'creative-tinkering': '#20c997',
            'funding': '#fd7e14', 'life-admin': '#6c757d', 'teaching': '#e83e8c',
            'supervision': '#17a2b8', 'Discovery': '#343a40', 'someday': '#868e96',
            'Inbox': '#00cc33', 'reading': '#ffcc00', 'book': '#ff6666',
            'home_stuff': '#66ccff'
        }
        
        # Create projects that don't exist
        existing_projects = {p.name: p for p in Project.query.all()}
        
        for project_name in projects_needed:
            if project_name not in existing_projects:
                color = project_colors.get(project_name, '#00cc33')
                project = Project(name=project_name, color=color)
                db.session.add(project)
                print(f"Creating project: {project_name} ({color})")
        
        db.session.commit()
        
        # Refresh project list
        existing_projects = {p.name: p for p in Project.query.all()}
        
        # Now import tasks
        print("\nImporting tasks...")
        tasks_imported = 0
        tasks_skipped = 0
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['TYPE'] != 'task':
                    continue
                
                task_name = row['CONTENT'].strip()
                if not task_name:
                    tasks_skipped += 1
                    continue
                
                # Parse dates
                due_date = parse_todoist_date(row['DATE']) or parse_todoist_date(row['DEADLINE'])
                
                # Convert priority
                priority = convert_todoist_priority(row['PRIORITY'])
                
                # Get project
                project_id = None
                if row['PROJECT'] and row['PROJECT'] in existing_projects:
                    project_id = existing_projects[row['PROJECT']].id
                
                # Create task
                task = Task(
                    name=task_name,
                    due_date=due_date,
                    priority=priority,
                    project_id=project_id,
                    completed=False  # Import all as active tasks
                )
                
                db.session.add(task)
                tasks_imported += 1
                
                if tasks_imported % 10 == 0:
                    print(f"  Imported {tasks_imported} tasks...")
        
        db.session.commit()
        
        print(f"\nImport complete!")
        print(f"  Tasks imported: {tasks_imported}")
        print(f"  Tasks skipped: {tasks_skipped}")
        print(f"  Projects created: {len(projects_needed - set(existing_projects.keys()))}")

if __name__ == '__main__':
    print("Todoist Import Script")
    print("====================")
    
    response = input("This will add data to your database. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Import cancelled.")
        sys.exit(0)
    
    try:
        import_todoist_data()
        print("\nDone! You can now start your Flask app to see the imported tasks.")
    except Exception as e:
        print(f"Error during import: {e}")
        import traceback
        traceback.print_exc()
