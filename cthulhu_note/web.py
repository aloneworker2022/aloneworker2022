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


class MemosConfigBody(BaseModel):
    url: Optional[str] = None
    token: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _csv() -> str:
    return _cfg.load().csv_path


def _data_dir() -> Path:
    return Path(_cfg.load().csv_path).expanduser().parent


def _settings_path() -> Path:
    return _data_dir() / "settings.json"


def _bg_dir() -> Path:
    d = _data_dir() / "backgrounds"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _card_img_dir() -> Path:
    d = _data_dir() / "card_images"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _has_card_image(item_id: int) -> bool:
    return (_card_img_dir() / f"{item_id}.jpg").exists()


def _to_dict(item) -> dict:
    return {
        "id": item.id,
        "content": item.content,
        "level": item.level,
        "parent_tag": item.parent_tag,
        "pinned": item.pinned,
        "created_at": item.created_at.isoformat(),
        "memos_id": item.memos_id,
        "has_image": _has_card_image(item.id),
    }


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


# ── API: complete (push to Memos then delete) ─────────────────────────────────

@app.post("/api/items/{item_id}/complete")
def complete_item(item_id: int):
    csv = _csv()
    items = _store.read_items(csv)
    item = next((i for i in items if i.id == item_id), None)
    if not item:
        raise HTTPException(404, "not found")

    memos_pushed = False
    memos_error: Optional[str] = None

    cfg = _cfg.load()
    if cfg.memos_token:
        from cthulhu_note.memos import MemosClient, MemosError
        client = MemosClient(cfg.memos_url, cfg.memos_token)
        try:
            client.push(item.content)
            memos_pushed = True
        except MemosError as e:
            memos_error = str(e)

    remaining = [i for i in items if i.id != item_id]
    _store.write_items(csv, remaining)
    return {"memos_pushed": memos_pushed, "memos_error": memos_error}


# ── API: memos config ─────────────────────────────────────────────────────────

@app.get("/api/memos/config")
def get_memos_config():
    cfg = _cfg.load()
    tok = cfg.memos_token
    masked = (("*" * max(0, len(tok) - 4)) + tok[-4:]) if len(tok) >= 4 else ("****" if tok else "")
    return {"url": cfg.memos_url, "token_set": bool(tok), "token_masked": masked}


@app.post("/api/memos/config")
def save_memos_config(body: MemosConfigBody):
    cfg = _cfg.load()
    if body.url is not None:
        cfg.memos_url = body.url.rstrip("/")
    if body.token:
        cfg.memos_token = body.token
    _cfg.save(cfg)
    return {"ok": True}


@app.get("/api/memos/test")
def test_memos():
    cfg = _cfg.load()
    if not cfg.memos_token:
        return {"ok": False, "error": "尚未設定 token"}
    from cthulhu_note.memos import MemosClient
    client = MemosClient(cfg.memos_url, cfg.memos_token)
    ok = client.test_connection()
    return {"ok": ok, "url": cfg.memos_url, "error": None if ok else "連線失敗"}


# ── API: card images ──────────────────────────────────────────────────────────

@app.post("/api/items/{item_id}/image", status_code=201)
async def upload_card_image(item_id: int, file: UploadFile = File(...)):
    data = await file.read()
    (_card_img_dir() / f"{item_id}.jpg").write_bytes(data)
    return {"ok": True}


@app.get("/api/items/{item_id}/image")
def serve_card_image(item_id: int):
    p = _card_img_dir() / f"{item_id}.jpg"
    if not p.exists():
        raise HTTPException(404, "no image")
    return FileResponse(str(p))


@app.delete("/api/items/{item_id}/image", status_code=204)
def delete_card_image(item_id: int):
    p = _card_img_dir() / f"{item_id}.jpg"
    if p.exists():
        p.unlink()


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
