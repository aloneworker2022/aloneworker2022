import json
import sys

import click

from cthulhu_note import config as config_mod
from cthulhu_note import storage
from cthulhu_note.state import Mode


@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="JSON 輸出（供 Hermes 呼叫）")
@click.pass_context
def main(ctx, use_json):
    """cthulhu-note — 瀑流等級 CLI bullet journal"""
    if ctx.invoked_subcommand is not None:
        ctx.ensure_object(dict)
        ctx.obj["use_json"] = use_json
        return

    if use_json:
        # --json with no subcommand → list
        _json_list()
        return

    cfg = config_mod.load()
    from cthulhu_note.app import build_app
    app = build_app(cfg, start_mode=Mode.INPUT)
    app.run()


@main.command()
@click.argument("text")
def add(text):
    """加入一個 Lv0 項目"""
    cfg = config_mod.load()
    item = storage.add_item(cfg.csv_path, text.strip(), level=0)
    click.echo(f"已加入 Lv0 #{item.id}：{item.content}")


@main.command()
def today():
    """印出代辦三格（唯讀）"""
    cfg = config_mod.load()
    items = storage.read_items(cfg.csv_path)
    pins = storage.pinned_items(items)
    if not pins:
        click.echo("（代辦三格空空的）")
        return
    for i, item in enumerate(pins, 1):
        click.echo(f"  {i}. {item.content}")


@main.command("process")
def process_cmd():
    """直接進入處理狀態"""
    cfg = config_mod.load()
    from cthulhu_note.app import build_app
    app = build_app(cfg, start_mode=Mode.PROCESS)
    app.run()


@main.command("list")
@click.pass_context
def list_cmd(ctx):
    """列出所有項目（--json 輸出 JSON）"""
    use_json = (ctx.obj or {}).get("use_json", False)
    _json_list() if use_json else _text_list()


def _json_list():
    cfg = config_mod.load()
    items = storage.read_items(cfg.csv_path)
    out = []
    for item in items:
        out.append({
            "id": item.id,
            "content": item.content,
            "level": item.level,
            "parent_tag": item.parent_tag,
            "pinned": item.pinned,
            "created_at": item.created_at.isoformat(),
            "memos_id": item.memos_id,
        })
    click.echo(json.dumps(out, ensure_ascii=False, indent=2))


def _text_list():
    cfg = config_mod.load()
    items = storage.read_items(cfg.csv_path)
    for item in items:
        pin = " [釘]" if item.pinned else ""
        click.echo(f"  Lv{item.level} #{item.id}{pin}  {item.content}")
