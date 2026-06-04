import json
import sys

import click

from cthulhu_note import config as config_mod
from cthulhu_note import storage
from cthulhu_note.config import Config
from cthulhu_note.memos import MemosClient
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
    cfg = _check_and_setup_memos(cfg)
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
    cfg = _check_and_setup_memos(cfg)
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


def _memos_setup_wizard(cfg: Config) -> Config:
    """對話式設定 Memos 連線，成功後寫回設定檔並回傳更新後的 Config。"""
    click.echo("")
    click.echo("── Memos 設定精靈 ──────────────────────")

    while True:
        url = click.prompt(
            f"Memos 網址",
            default=cfg.memos_url,
        ).strip().rstrip("/")

        token = click.prompt("Access token", hide_input=True).strip()

        click.echo("正在測試連線…", nl=False)
        client = MemosClient(url, token)
        ok = client.test_connection()

        if ok:
            click.echo(" 連線成功！")
            cfg.memos_url = url
            cfg.memos_token = token
            config_mod.save(cfg)
            click.echo(f"設定已寫入 {config_mod._resolve()}")
            click.echo("────────────────────────────────────")
            click.echo("")
            return cfg
        else:
            click.echo(" 連線失敗。")
            retry = click.confirm("要重新輸入嗎？", default=True)
            if not retry:
                click.echo("跳過設定，Lv1 完成功能本次停用。")
                click.echo("────────────────────────────────────")
                click.echo("")
                return cfg


def _check_and_setup_memos(cfg: Config) -> Config:
    """啟動時檢查 Memos 連線，失敗則進入設定精靈。"""
    if not cfg.memos_token:
        click.echo("尚未設定 Memos token，進入設定精靈…")
        return _memos_setup_wizard(cfg)

    client = MemosClient(cfg.memos_url, cfg.memos_token)
    if not client.test_connection():
        click.echo(f"Memos 無法連線（{cfg.memos_url}），進入設定精靈…")
        return _memos_setup_wizard(cfg)

    return cfg


def _text_list():
    cfg = config_mod.load()
    items = storage.read_items(cfg.csv_path)
    for item in items:
        pin = " [釘]" if item.pinned else ""
        click.echo(f"  Lv{item.level} #{item.id}{pin}  {item.content}")
