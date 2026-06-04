import csv
import fcntl
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from cthulhu_note.models import BujoItem

LV1_LIMIT = 10
PIN_LIMIT = 3

CSV_FIELDS = ["id", "content", "level", "parent_tag", "pinned", "created_at", "memos_id"]


def _resolve_path(csv_path: str) -> Path:
    return Path(csv_path).expanduser()


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _item_to_row(item: BujoItem) -> dict:
    return {
        "id": item.id,
        "content": item.content,
        "level": item.level,
        "parent_tag": item.parent_tag,
        "pinned": str(item.pinned).lower(),
        "created_at": item.created_at.isoformat(),
        "memos_id": item.memos_id,
    }


def _row_to_item(row: dict) -> BujoItem:
    return BujoItem(
        id=int(row["id"]),
        content=row["content"],
        level=int(row["level"]),
        parent_tag=row["parent_tag"],
        pinned=row["pinned"].lower() == "true",
        created_at=datetime.fromisoformat(row["created_at"]),
        memos_id=row["memos_id"],
    )


def read_items(csv_path: str) -> list[BujoItem]:
    path = _resolve_path(csv_path)
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            reader = csv.DictReader(f)
            return [_row_to_item(row) for row in reader]
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def write_items(csv_path: str, items: list[BujoItem]) -> None:
    path = _resolve_path(csv_path)
    bak = path.with_suffix(".csv.bak")
    _ensure_dir(path)

    # backup existing file
    if path.exists():
        shutil.copy2(path, bak)

    tmp = path.with_suffix(".csv.tmp")
    try:
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                writer.writeheader()
                for item in items:
                    writer.writerow(_item_to_row(item))
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        os.replace(tmp, path)
    except Exception:
        # rollback
        if bak.exists():
            shutil.copy2(bak, path)
        if tmp.exists():
            tmp.unlink()
        raise


def next_id(items: list[BujoItem]) -> int:
    if not items:
        return 1
    return max(item.id for item in items) + 1


def add_item(
    csv_path: str,
    content: str,
    level: int,
    parent_tag: str = "",
    pinned: bool = False,
) -> BujoItem:
    items = read_items(csv_path)
    new_item = BujoItem(
        id=next_id(items),
        content=content,
        level=level,
        parent_tag=parent_tag,
        pinned=pinned,
        created_at=datetime.now(timezone.utc),
        memos_id="",
    )
    items.append(new_item)
    write_items(csv_path, items)
    return new_item


def lv1_count(items: list[BujoItem]) -> int:
    return sum(1 for i in items if i.level == 1)


def pin_count(items: list[BujoItem]) -> int:
    return sum(1 for i in items if i.level == 1 and i.pinned)


def pinned_items(items: list[BujoItem]) -> list[BujoItem]:
    return [i for i in items if i.level == 1 and i.pinned]
