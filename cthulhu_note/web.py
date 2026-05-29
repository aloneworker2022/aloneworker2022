from __future__ import annotations

from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from cthulhu_note import config as _cfg
from cthulhu_note import storage as _store

app = FastAPI()

_HTML = (Path(__file__).parent / "web_template.html").read_text(encoding="utf-8")


# ── HTML ──────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index():
    return _HTML


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateBody(BaseModel):
    content: str
    level: int = 0
    parent_tag: str = ""
    pinned: bool = False


class UpdateBody(BaseModel):
    content: Optional[str] = None
    level: Optional[int] = None
    pinned: Optional[bool] = None
    parent_tag: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _csv() -> str:
    return _cfg.load().csv_path


def _to_dict(item) -> dict:
    return {
        "id": item.id,
        "content": item.content,
        "level": item.level,
        "parent_tag": item.parent_tag,
        "pinned": item.pinned,
        "created_at": item.created_at.isoformat(),
        "memos_id": item.memos_id,
    }


# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/api/items")
def list_items(level: Optional[int] = None):
    items = _store.read_items(_csv())
    if level is not None:
        items = [i for i in items if i.level == level]
    return [_to_dict(i) for i in items]


@app.post("/api/items", status_code=201)
def create_item(body: CreateBody):
    item = _store.add_item(_csv(), body.content, body.level, body.parent_tag, body.pinned)
    return _to_dict(item)


@app.delete("/api/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    csv = _csv()
    items = _store.read_items(csv)
    remaining = [i for i in items if i.id != item_id]
    if len(remaining) == len(items):
        raise HTTPException(404, "not found")
    _store.write_items(csv, remaining)


@app.patch("/api/items/{item_id}")
def update_item(item_id: int, body: UpdateBody):
    csv = _csv()
    items = _store.read_items(csv)
    item = next((i for i in items if i.id == item_id), None)
    if not item:
        raise HTTPException(404, "not found")
    if body.content is not None:
        item.content = body.content
    if body.level is not None:
        item.level = body.level
    if body.pinned is not None:
        item.pinned = body.pinned
    if body.parent_tag is not None:
        item.parent_tag = body.parent_tag
    _store.write_items(csv, items)
    return _to_dict(item)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    uvicorn.run(app, host="0.0.0.0", port=9968, reload=False)


if __name__ == "__main__":
    main()
