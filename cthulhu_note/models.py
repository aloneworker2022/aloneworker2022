from dataclasses import dataclass
from datetime import datetime


@dataclass
class BujoItem:
    id: int
    content: str
    level: int
    parent_tag: str
    pinned: bool
    created_at: datetime
    memos_id: str
