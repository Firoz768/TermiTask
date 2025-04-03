import sqlite3
import pandas as pd

def export_to_csv(filename: str = "tasks_export.csv") -> None:
    """Export all tasks to CSV"""
    conn = sqlite3.connect("tasks.db")
    df = pd.read_sql_query("SELECT * FROM tasks", conn)
    df.to_csv(filename, index=False)
    conn.close()