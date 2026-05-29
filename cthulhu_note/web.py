from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
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


def _data_dir() -> Path:
    return Path(_cfg.load().csv_path).expanduser().parent


def _settings_path() -> Path:
    return _data_dir() / "settings.json"


def _bg_dir() -> Path:
    d = _data_dir() / "backgrounds"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── API: items ────────────────────────────────────────────────────────────────

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


# ── API: settings ─────────────────────────────────────────────────────────────

@app.get("/api/settings")
def get_settings():
    p = _settings_path()
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


@app.post("/api/settings")
async def save_settings(request: Request):
    body = await request.json()
    p = _settings_path()
    p.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    return body


# ── API: backgrounds ──────────────────────────────────────────────────────────

@app.post("/api/backgrounds", status_code=201)
async def upload_bg(file: UploadFile = File(...)):
    ext = Path(file.filename or "img.jpg").suffix.lower() or ".jpg"
    name = uuid.uuid4().hex + ext
    data = await file.read()
    (_bg_dir() / name).write_bytes(data)
    return {"name": name}


@app.get("/api/backgrounds/{name}")
def serve_bg(name: str):
    p = _bg_dir() / name
    if not p.exists():
        raise HTTPException(404, "not found")
    return FileResponse(str(p))


@app.delete("/api/backgrounds/{name}", status_code=204)
def delete_bg(name: str):
    p = _bg_dir() / name
    if p.exists():
        p.unlink()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    uvicorn.run(app, host="0.0.0.0", port=3788, reload=False)


if __name__ == "__main__":
    main()
