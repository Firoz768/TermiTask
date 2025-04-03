import click
from datetime import datetime
from typing import List
from database import db
import sys
import platform
from utils import reminders

@click.group()
@click.option('--verbose', is_flag=True, help='Enable debug logging')
def cli(verbose):
    """Advanced CLI Task Manager with Collaboration"""
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

# ----- User Management -----
@cli.command()
@click.argument("username")
@click.argument("email")
@click.argument("password")
def register(username, email, password):
    """Register a new user"""
    if len(password) < 8:
        click.echo("❌ Password must be at least 8 characters")
        return
        
    if db.create_user(username, email, password):
        click.echo(f"✅ User {username} registered")
    else:
        click.echo("❌ Registration failed (username/email may exist)")

@cli.command()
@click.argument("username")
@click.argument("password")
def login(username, password):
    """Authenticate a user"""
    if db.authenticate_user(username, password):
        click.echo(f"✅ Authenticated as {username}")
    else:
        click.echo("❌ Invalid credentials")

# ----- Task Management -----
@cli.command()
@click.argument("title")
@click.option("--description", help="Task description")
@click.option("--due-date", help="Due date (YYYY-MM-DD)")
@click.option("--priority", default="medium", 
              type=click.Choice(["low", "medium", "high", "critical"]))
@click.option("--tag", "-t", multiple=True)
@click.option("--recurrence", type=click.Choice(["daily", "weekly", "monthly"]))
@click.option("--created-by", required=True, help="Task owner username")
@click.option("--assign-to", help="Assignee username")
def add(title, description, due_date, priority, tag, recurrence, created_by, assign_to):
    """Add a new task"""
    try:
        if due_date:
            datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        click.echo("❌ Invalid date format. Use YYYY-MM-DD")
        return

    task_data = {
        "title": title,
        "description": description or "",
        "due_date": due_date,
        "priority": priority,
        "tags": list(tag),
        "recurrence": recurrence,
        "created_by": created_by,
        "assigned_to": assign_to
    }
    task_id = db.create_task(task_data)
    if task_id:
        click.echo(f"✅ Task created [ID: {task_id}]")
    else:
        click.echo("❌ Task creation failed")

@cli.command(name="list")
@click.option("--username", help="Filter tasks for specific user")
@click.option("--priority", help="Filter by priority level")
@click.option("--status", help="Filter by status (pending/completed)")
@click.option("--overdue", is_flag=True, help="Show only overdue tasks")
@click.option("--search", help="Search in task titles/descriptions")
@click.option("--tag", multiple=True, help="Filter by tags")
@click.option("--sort", type=click.Choice(["due_date", "priority", "created_at"]), 
              default="due_date", help="Sorting field")
@click.option("--reverse", is_flag=True, help="Reverse sort order")
def list_tasks(username, priority, status, overdue, search, tag, sort, reverse):
    """List tasks with filters"""
    filters = {
        "username": username,
        "priority": priority,
        "status": status,
        "search": search,
        "tags": list(tag)
    }
    
    tasks = db.get_tasks(filters, sort, reverse)
    
    if overdue:
        now = datetime.now().isoformat()
        tasks = [t for t in tasks if t.get("due_date") and t["due_date"] < now and t["status"] != "completed"]
    
    if not tasks:
        click.echo("No tasks found")
        return
        
    for task in tasks:
        due_date = datetime.fromisoformat(task["due_date"]).strftime("%Y-%m-%d") if task.get("due_date") else "None"
        click.echo(f"""
📌 {task['title']} [ID: {task['id']}]
   Status: {task['status'].capitalize()}
   Priority: {task['priority'].capitalize()}
   Due: {due_date}
   Created By: {task['created_by']}
   Assigned To: {task.get('assigned_to', 'Unassigned')}
   Tags: {', '.join(task['tags'].split(',')) if task.get('tags') else 'None'}""")

@cli.command()
@click.argument("task_id")
@click.option("--status", type=click.Choice(["pending", "completed"]))
@click.option("--due-date", help="New due date (YYYY-MM-DD)")
@click.option("--priority", type=click.Choice(["low", "medium", "high", "critical"]))
@click.option("--tag", "-t", multiple=True)
@click.option("--description", help="New description")
def update(task_id, status, due_date, priority, tag, description):
    """Update an existing task"""
    if not task_id or len(task_id) != 36:
        click.echo("❌ Invalid task ID format")
        return
        
    updates = {}
    if status: updates["status"] = status
    if due_date:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
            updates["due_date"] = due_date
        except ValueError:
            click.echo("❌ Invalid date format. Use YYYY-MM-DD")
            return
    if priority: updates["priority"] = priority
    if tag: updates["tags"] = ",".join(tag)
    if description: updates["description"] = description
    
    if not updates:
        click.echo("❌ No updates provided")
        return
        
    if db.update_task(task_id, updates):
        click.echo(f"✅ Task {task_id} updated")
    else:
        click.echo("❌ Update failed")

@cli.command()
@click.argument("task_id")
def delete(task_id):
    """Delete a task permanently"""
    if not task_id or len(task_id) != 36:
        click.echo("❌ Invalid task ID format")
        return
        
    if db.delete_task(task_id):
        click.echo(f"✅ Task {task_id} deleted")
    else:
        click.echo("❌ Deletion failed")

# ----- Collaboration Commands -----
@cli.command()
@click.argument("task_id")
@click.argument("assigner")
@click.argument("assignee")
def assign(task_id, assigner, assignee):
    """Assign task to another user"""
    if not task_id or len(task_id) != 36:
        click.echo("❌ Invalid task ID format")
        return
        
    if db.assign_task(task_id, assigner, assignee):
        click.echo(f"✅ Task {task_id} assigned to {assignee}")
    else:
        click.echo("❌ Assignment failed (task not found or invalid permissions)")

@cli.command()
@click.argument("username")
def workload(username):
    """Show user's task workload"""
    tasks = db.get_user_tasks(username)
    
    status_counts = {"pending": 0, "completed": 0}
    priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    
    for task in tasks:
        status_counts[task["status"]] += 1
        priority_counts[task["priority"]] += 1
    
    click.echo(f"\n📊 Workload Report for {username}")
    click.echo("--------------------------------")
    click.echo(f"Total Tasks: {len(tasks)}")
    click.echo(f"Pending: {status_counts['pending']} | Completed: {status_counts['completed']}")
    click.echo("\nPriority Breakdown:")
    for prio, count in priority_counts.items():
        click.echo(f"  {prio.capitalize()}: {count}")

# ----- Reporting Commands -----
@cli.command()
@click.argument("username")
@click.option("--output", default="productivity.png", help="Output image file")
def report(username, output):
    """Generate productivity report with visualization"""
    try:
        from utils.stats import get_user_productivity
        from utils.visualizations import generate_productivity_chart
        
        stats = get_user_productivity(username)
        
        click.echo(f"""
📈 Productivity Report for {username}
================================
✅ Completion Rate: {stats['completion_rate']:.0%}
⏰ Overdue Tasks: {stats['overdue_tasks']}
📌 Priority Distribution:
   Critical: {stats['priority_distribution']['critical']}
   High: {stats['priority_distribution']['high']}
   Medium: {stats['priority_distribution']['medium']}
   Low: {stats['priority_distribution']['low']}
""")
        if generate_productivity_chart(username, output):
            click.echo(f"📊 Visualization saved to {output}")
        else:
            click.echo("❌ Failed to generate chart")
    except ImportError as e:
        click.echo(f"❌ Missing dependencies: {str(e)}\nRun: pip install matplotlib pandas")
    except Exception as e:
        click.echo(f"❌ Report generation failed: {str(e)}")

@cli.command()
@click.argument("filename", default="tasks.csv")
def export(filename):
    """Export tasks to CSV"""
    try:
        from utils.reports import export_to_csv
        export_to_csv(filename)
        click.echo(f"✅ Tasks exported to {filename}")
    except ImportError:
        click.echo("❌ Error: pandas package not installed. Run: pip install pandas")
    except Exception as e:
        click.echo(f"❌ Export failed: {str(e)}")

# ----- System Commands -----
@cli.command()
def process_recurring():
    """Process recurring tasks (run via cron)"""
    from utils.reminders import check_and_update_recurring_tasks
    check_and_update_recurring_tasks()
    click.echo("✅ Recurring tasks processed")

@cli.command()
@click.argument("backup_file", type=click.Path())
def backup(backup_file):
    """Create database backup"""
    try:
        db.backup(backup_file)
        click.echo(f"✅ Backup created at {backup_file}")
    except Exception as e:
        click.echo(f"❌ Backup failed: {str(e)}")

@cli.command()
@click.argument("backup_file", type=click.Path(exists=True))
def restore(backup_file):
    """Restore from backup"""
    try:
        db.restore(backup_file)
        click.echo(f"✅ Restored from {backup_file}")
    except Exception as e:
        click.echo(f"❌ Restore failed: {str(e)}")

# ----- Settings Management -----
@cli.command()
@click.argument("username")
@click.option("--theme", type=click.Choice(["light", "dark"]), help="Interface theme")
@click.option("--date-format", default="%Y-%m-%d", help="Date display format")
@click.option("--notifications/--no-notifications", default=True, help="Enable notifications")
def settings(username, theme, date_format, notifications):
    """Configure user preferences"""
    prefs = {
        "theme": theme,
        "date_format": date_format,
        "notifications": notifications
    }
    if db.save_settings(username, prefs):
        click.echo("✅ Settings updated")
    else:
        click.echo("❌ Failed to save settings")

if __name__ == "__main__":
    cli()