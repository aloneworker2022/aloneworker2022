"""
cthulhu-note skill for AI agents (openclaw / Hermes / any function-calling agent).

Import this module and register the functions below as tools.
The agent can then read, add, delete, and update items in the user's bujo.csv.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from cthulhu_note import config as _cfg
from cthulhu_note import storage as _store

# ── skill description (paste into your agent's system prompt) ─────────────────

SKILL_DESCRIPTION = """
# cthulhu-note skill

You have access to the user's personal GTD (bullet journal) system called cthulhu-note.
The data lives in a CSV file at: ~/.local/share/cthulhu-note/bujo.csv

## Item levels
- **Lv0** – inbox, things just captured, not yet processed
- **Lv1** – active tasks (max 10), being worked on
- **Lv2** – sub-tasks that belong to a Lv1 item (tagged with [parent])
- **Lv3** – long-term reference / memory items

## Pinned items (代辦三格)
Up to 3 Lv1 items can be pinned. These are the user's "top 3 focus" for today.

## Available tools
- `bujo_list`   – list all items (optionally filter by level)
- `bujo_add`    – add a new item
- `bujo_delete` – delete an item by id
- `bujo_update` – update content / level / pinned of an item

## Conversation tips
- When the user says things like "幫我加 X", call bujo_add(content="X", level=0)
- When they say "刪掉 X" or "刪 #ID", call bujo_delete(id=...)
- When they say "今天要做什麼" or "代辦", call bujo_list() and highlight pinned Lv1 items
- When they say "完成了 X", call bujo_delete to remove it
- When they say "改 X 的內容", call bujo_update
- Always confirm actions back to the user in Traditional Chinese
"""


# ── helpers ───────────────────────────────────────────────────────────────────

def _csv_path() -> str:
    return _cfg.load().csv_path


def _item_to_dict(item) -> dict:
    return {
        "id": item.id,
        "content": item.content,
        "level": item.level,
        "parent_tag": item.parent_tag,
        "pinned": item.pinned,
        "created_at": item.created_at.isoformat(),
        "memos_id": item.memos_id,
    }


# ── tool functions ────────────────────────────────────────────────────────────

def bujo_list(level: Optional[int] = None) -> str:
    """List items in the user's cthulhu-note bujo.

    Args:
        level: Filter by level (0=inbox, 1=active, 2=sub-task, 3=reference).
               Omit to return all items.

    Returns:
        JSON string with a list of items.
        Each item has: id, content, level, parent_tag, pinned, created_at, memos_id
    """
    items = _store.read_items(_csv_path())
    if level is not None:
        items = [i for i in items if i.level == level]
    return json.dumps([_item_to_dict(i) for i in items], ensure_ascii=False, indent=2)


def bujo_add(content: str, level: int = 0, parent_tag: str = "", pinned: bool = False) -> str:
    """Add a new item to the user's cthulhu-note bujo.

    Args:
        content:    The text of the item.
        level:      Level to create at (default 0 = inbox).
        parent_tag: Parent tag for Lv2 sub-tasks (e.g. "買東西").
        pinned:     Whether to pin this item as one of the 代辦三格 (max 3).

    Returns:
        JSON string of the newly created item.
    """
    item = _store.add_item(_csv_path(), content=content, level=level,
                           parent_tag=parent_tag, pinned=pinned)
    return json.dumps(_item_to_dict(item), ensure_ascii=False, indent=2)


def bujo_delete(id: int) -> str:
    """Delete an item from the user's cthulhu-note bujo by its id.

    Args:
        id: The numeric id of the item to delete.

    Returns:
        "ok" on success, or an error message if the id was not found.
    """
    csv = _csv_path()
    items = _store.read_items(csv)
    remaining = [i for i in items if i.id != id]
    if len(remaining) == len(items):
        return f"error: id {id} not found"
    _store.write_items(csv, remaining)
    return "ok"


def bujo_update(
    id: int,
    content: Optional[str] = None,
    level: Optional[int] = None,
    pinned: Optional[bool] = None,
    parent_tag: Optional[str] = None,
) -> str:
    """Update an existing item in the user's cthulhu-note bujo.

    Args:
        id:         The numeric id of the item to update.
        content:    New text content (leave None to keep existing).
        level:      New level 0-3 (leave None to keep existing).
        pinned:     New pinned state (leave None to keep existing).
        parent_tag: New parent tag (leave None to keep existing).

    Returns:
        JSON string of the updated item, or an error message.
    """
    csv = _csv_path()
    items = _store.read_items(csv)
    target = next((i for i in items if i.id == id), None)
    if target is None:
        return f"error: id {id} not found"

    if content is not None:
        target.content = content
    if level is not None:
        target.level = level
    if pinned is not None:
        target.pinned = pinned
    if parent_tag is not None:
        target.parent_tag = parent_tag

    _store.write_items(csv, items)
    return json.dumps(_item_to_dict(target), ensure_ascii=False, indent=2)


# ── tool registry (for agent frameworks that want a list of callables) ────────

TOOLS = [bujo_list, bujo_add, bujo_delete, bujo_update]
