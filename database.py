import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import bcrypt
import logging
from uuid import uuid4
import shutil
import os
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database schema safely"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Users Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    settings TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tasks Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    due_date TEXT,
                    priority TEXT NOT NULL DEFAULT 'medium'
                        CHECK(priority IN ('low', 'medium', 'high', 'critical')),
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK(status IN ('pending', 'completed')),
                    tags TEXT,
                    recurrence TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT NOT NULL,
                    assigned_to TEXT
                )
            """)
            
            # Indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_priority 
                ON tasks(priority)
            """)
            conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get configured database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    # User Management
    def create_user(self, username: str, email: str, password: str) -> bool:
        """Create a new user account"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO users (username, email, hashed_password)
                    VALUES (?, ?, ?)
                """, (
                    username,
                    email,
                    bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError as e:
            logger.error(f"User creation failed: {str(e)}")
            return False

    def authenticate_user(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT hashed_password FROM users WHERE username = ?
            """, (username,))
            result = cursor.fetchone()
            if not result:
                return False
            return bcrypt.checkpw(password.encode(), result[0].encode())

    # Task Management
    def create_task(self, task_data: Dict) -> Optional[str]:
        """Create a new task"""
        if not task_data.get("title") or not task_data.get("created_by"):
            logger.error("Missing required fields: title and created_by")
            return None

        task_id = str(uuid4())
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO tasks (
                        id, title, description, due_date, priority, status, 
                        tags, recurrence, created_by, assigned_to
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id,
                    task_data["title"],
                    task_data.get("description", ""),
                    task_data.get("due_date"),
                    task_data.get("priority", "medium"),
                    task_data.get("status", "pending"),
                    ",".join(task_data["tags"]) if isinstance(task_data.get("tags"), list) else task_data.get("tags", ""),
                    task_data.get("recurrence"),
                    task_data["created_by"],
                    task_data.get("assigned_to")
                ))
                conn.commit()
                return task_id
        except sqlite3.Error as e:
            logger.error(f"Task creation failed: {str(e)}")
            return None

    def get_tasks(self, filters: Dict = None, sort: str = "due_date", reverse: bool = False) -> List[Dict]:
        """Get tasks with advanced filtering and sorting"""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        if filters:
            if filters.get("username"):
                query += " AND (created_by = ? OR assigned_to = ?)"
                params.extend([filters["username"]] * 2)
            if filters.get("search"):
                query += " AND (title LIKE ? OR description LIKE ?)"
                params.extend([f"%{filters['search']}%"] * 2)
            if filters.get("tags"):
                query += " AND (" + " OR ".join(["tags LIKE ?" for _ in filters["tags"]]) + ")"
                params.extend([f"%{tag}%" for tag in filters["tags"]])
            if filters.get("priority"):
                query += " AND priority = ?"
                params.append(filters["priority"])
            if filters.get("status"):
                query += " AND status = ?"
                params.append(filters["status"])
        
        # Sorting
        sort_order = "DESC" if reverse else "ASC"
        query += f" ORDER BY {sort} {sort_order}"
        
        with self._get_connection() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def update_task(self, task_id: str, updates: dict) -> bool:
        """Update an existing task"""
        try:
            with self._get_connection() as conn:
                set_clause = ", ".join([f"{k} = ?" for k in updates])
                values = list(updates.values()) + [task_id]
                conn.execute(f"""
                    UPDATE tasks 
                    SET {set_clause}
                    WHERE id = ?
                """, values)
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Update failed: {str(e)}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a task permanently"""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Deletion failed: {str(e)}")
            return False

    # User-specific methods
    def get_user_tasks(self, username: str) -> List[Dict]:
        """Get all tasks visible to a user"""
        return self.get_tasks({"username": username})

    def get_user_settings(self, username: str) -> Dict:
        """Get user settings"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT settings FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            if result and result[0]:
                try:
                    return json.loads(result[0])
                except json.JSONDecodeError:
                    return {}
            return {}

    def save_settings(self, username: str, settings: Dict) -> bool:
        """Save user preferences"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE users SET settings = ?
                    WHERE username = ?
                """, (json.dumps(settings), username))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Settings save failed: {str(e)}")
            return False

    # Collaboration
    def assign_task(self, task_id: str, assigner: str, assignee: str) -> bool:
        """Assign task to another user"""
        try:
            with self._get_connection() as conn:
                # Verify assignee exists
                if not conn.execute("SELECT 1 FROM users WHERE username = ?", (assignee,)).fetchone():
                    return False
                
                # Verify assigner owns the task
                result = conn.execute(
                    "UPDATE tasks SET assigned_to = ? WHERE id = ? AND created_by = ?",
                    (assignee, task_id, assigner)
                )
                conn.commit()
                return result.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Assignment failed: {str(e)}")
            return False

    # Backup/Restore
    def backup(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            return False

    def restore(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            shutil.copy2(backup_path, self.db_path)
            return True
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return False

# Initialize database
db = DatabaseManager()