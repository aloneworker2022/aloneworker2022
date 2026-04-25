import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path("~/.config/cthulhu-note/config.toml")

DEFAULT_TOML = """\
[memos]
url = "http://localhost:5230"
token = ""  # Set your Memos access token here

[data]
csv_path = "~/.local/share/cthulhu-note/bujo.csv"

[display]
lv3_flash_enabled = true
lv3_flash_probability = 0.05
lv3_flash_duration = 0.6
"""


@dataclass
class Config:
    memos_url: str
    memos_token: str
    csv_path: str
    lv3_flash_enabled: bool
    lv3_flash_probability: float
    lv3_flash_duration: float


def _resolve() -> Path:
    return CONFIG_PATH.expanduser()


def save(config: Config) -> None:
    path = _resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""\
[memos]
url = "{config.memos_url}"
token = "{config.memos_token}"

[data]
csv_path = "{config.csv_path}"

[display]
lv3_flash_enabled = {str(config.lv3_flash_enabled).lower()}
lv3_flash_probability = {config.lv3_flash_probability}
lv3_flash_duration = {config.lv3_flash_duration}
"""
    path.write_text(content, encoding="utf-8")


def load() -> Config:
    path = _resolve()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_TOML, encoding="utf-8")

    with open(path, "rb") as f:
        data = tomllib.load(f)

    return Config(
        memos_url=data["memos"]["url"],
        memos_token=data["memos"]["token"],
        csv_path=data["data"]["csv_path"],
        lv3_flash_enabled=data["display"]["lv3_flash_enabled"],
        lv3_flash_probability=data["display"]["lv3_flash_probability"],
        lv3_flash_duration=data["display"]["lv3_flash_duration"],
    )
