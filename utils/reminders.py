from datetime import datetime, timedelta
from database import db
import schedule
import time

def calculate_next_occurrence(due_date: datetime, recurrence: str) -> datetime:
    """Calculate next occurrence date for recurring tasks"""
    if recurrence == "daily":
        return due_date + timedelta(days=1)
    elif recurrence == "weekly":
        return due_date + timedelta(weeks=1)
    elif recurrence == "monthly":
        return (due_date.replace(day=1) + timedelta(days=32)).replace(day=due_date.day)
    return due_date

def check_and_update_recurring_tasks():
    """Process all recurring tasks"""
    for task in db.get_tasks({"recurrence": True}):
        if task['due_date'] and datetime.fromisoformat(task['due_date']) <= datetime.now():
            updated_task = task.copy()
            updated_task['due_date'] = calculate_next_occurrence(
                datetime.fromisoformat(task['due_date']),
                task['recurrence']
            ).isoformat()
            db.update_task(task['id'], updated_task)

def start_reminder_daemon(interval_minutes: int = 5):
    """Run reminders in background"""
    schedule.every(interval_minutes).minutes.do(check_and_update_recurring_tasks)
    
    while True:
        schedule.run_pending()
        time.sleep(1)