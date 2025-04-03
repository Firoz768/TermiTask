from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid

# Models
@dataclass
class User:
    username: str
    email: str
    hashed_password: str = field(repr=False)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Task:
    title: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    due_date: Optional[datetime] = None
    priority: str = "medium"
    status: str = "pending"
    tags: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    recurrence: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

# Serialization
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'priority': self.priority,
            'status': self.status,
            'tags': self.tags,
            'assigned_to': self.assigned_to,
            'recurrence': self.recurrence
        }