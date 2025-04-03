"""Utility functions for statistics"""
from datetime import datetime
from database import db  

def get_user_productivity(username: str) -> dict:
    """Calculate completion statistics with date validation"""
    tasks = db.get_tasks({"username": username})
    
    completed = [t for t in tasks if t['status'] == 'completed']
    
    # Safely check overdue tasks
    overdue = []
    for task in tasks:
        if task['status'] != 'completed' and task.get('due_date'):
            try:
                if datetime.fromisoformat(task['due_date']) < datetime.now():
                    overdue.append(task)
            except (ValueError, TypeError):
                continue
    
    # Initialize priority distribution
    priority_distribution = {
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0
    }
    
    # Calculate priority distribution
    for task in tasks:
        priority = task.get('priority', 'medium').lower()
        if priority in priority_distribution:
            priority_distribution[priority] += 1
    
    return {
        'total_tasks': len(tasks),
        'completion_rate': len(completed)/len(tasks) if tasks else 0,
        'overdue_tasks': len(overdue),
        'priority_distribution': priority_distribution
    }