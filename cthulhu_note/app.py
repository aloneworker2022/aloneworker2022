import asyncio
from datetime import datetime, timezone

from prompt_toolkit import Application
from prompt_toolkit.output import create_output

from cthulhu_note import storage
from cthulhu_note.config import Config
from cthulhu_note.keybindings import build_bindings
from cthulhu_note.layout import build_layout
from cthulhu_note.memos import MemosClient, MemosError
from cthulhu_note.models import BujoItem
from cthulhu_note.state import AppState, Mode


class Handlers:
    def __init__(self, state: AppState, config: Config, memos: MemosClient | None, app_ref: list) -> None:
        self._state = state
        self._config = config
        self._memos = memos
        self._app_ref = app_ref  # mutable list so we can inject app after creation

    @property
    def _app(self):
        return self._app_ref[0]

    def _invalidate(self):
        self._app.invalidate()

    def _save(self):
        storage.write_items(self._config.csv_path, self._state.items)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _go_input(self, message: str = ""):
        s = self._state
        s.mode = Mode.INPUT
        s.message = message
        s.input_buffer = ""
        s.cards = []
        s.card_index = 0
        s.cut_card = None
        self._invalidate()

    def _load_level(self, level: int) -> bool:
        s = self._state
        cards = s.cards_for_level(level)
        if not cards:
            return False
        s.process_level = level
        s.cards = cards
        s.card_index = 0
        return True

    def _advance_card(self):
        s = self._state
        s.card_index += 1
        if s.card_index >= len(s.cards):
            self._next_level()

    def _next_level(self):
        s = self._state
        s.message = ""
        from cthulhu_note import flash as flash_mod
        if s.process_level == 0:
            flash_mod.maybe_flash(s.items, self._config, self._app)
            if not self._load_level(1):
                if not self._load_level(2):
                    self._go_input()
        elif s.process_level == 1:
            flash_mod.maybe_flash(s.items, self._config, self._app)
            if not self._load_level(2):
                self._go_input()
        else:
            self._go_input()
        self._invalidate()

    # ── INPUT ─────────────────────────────────────────────────────────────────

    def input_char(self, ch: str):
        if ch and ch.isprintable():
            self._state.input_buffer += ch
            self._state.message = ""
            self._invalidate()

    def input_backspace(self):
        if self._state.input_buffer:
            self._state.input_buffer = self._state.input_buffer[:-1]
            self._invalidate()

    def input_enter(self):
        s = self._state
        text = s.input_buffer.strip()
        if not text:
            return
        new_item = BujoItem(
            id=storage.next_id(s.items),
            content=text,
            level=0,
            parent_tag="",
            pinned=False,
            created_at=datetime.now(timezone.utc),
            memos_id="",
        )
        s.items.append(new_item)
        self._save()
        s.input_buffer = ""
        s.message = ""
        self._invalidate()

    def input_tab(self):
        s = self._state
        s.message = ""
        s.input_buffer = ""
        if not self._load_level(0):
            if not self._load_level(1):
                if not self._load_level(2):
                    self._go_input()
                    return
        s.mode = Mode.PROCESS
        from cthulhu_note import flash as flash_mod
        flash_mod.maybe_flash(s.items, self._config, self._app)
        self._invalidate()

    # ── CTRL+V ───────────────────────────────────────────────────────────────

    def ctrl_v_open(self):
        s = self._state
        s.mode = Mode.CTRL_V
        s.ctrl_v_cursor = 0
        s.message = ""
        self._invalidate()

    def ctrl_v_move(self, delta: int):
        s = self._state
        pins = s.pinned_items
        if not pins:
            return
        s.ctrl_v_cursor = (s.ctrl_v_cursor + delta) % len(pins)
        self._invalidate()

    def ctrl_v_enter(self):
        s = self._state
        pins = s.pinned_items
        if not pins:
            self._go_input()
            return
        idx = s.ctrl_v_cursor
        if idx >= len(pins):
            idx = 0
        item = pins[idx]
        self._complete_item(item)

    def ctrl_v_close(self):
        s = self._state
        s.mode = Mode.INPUT
        s.message = ""
        self._invalidate()

    def _complete_item(self, item: BujoItem):
        s = self._state
        if not s.memos_available or self._memos is None:
            s.message = "Memos 無法連線，無法完成"
            self._invalidate()
            return
        try:
            uid = self._memos.push(item.content)
            s.items = [i for i in s.items if i.id != item.id]
            self._save()
            s.mode = Mode.INPUT
            s.message = ""
            from cthulhu_note import flash as flash_mod
            flash_mod.maybe_flash(s.items, self._config, self._app)
        except MemosError as e:
            s.message = f"推送失敗，稍後重試（{e}）"
            s.mode = Mode.INPUT
        self._invalidate()

    # ── PROCESS Lv0 ──────────────────────────────────────────────────────────

    def lv0_o(self):
        s = self._state
        card = s.current_card
        if card is None:
            return
        if s.lv1_count >= 10:
            self._go_input("Lv1 已滿 10 格，請先處理")
            return
        card.level = 1
        self._save()
        s.cards = [c for c in s.cards if c.id != card.id]
        if s.card_index >= len(s.cards):
            self._next_level()
        else:
            self._invalidate()

    def lv0_x(self):
        s = self._state
        card = s.current_card
        if card is None:
            return
        s.items = [i for i in s.items if i.id != card.id]
        self._save()
        s.cards = [c for c in s.cards if c.id != card.id]
        if s.card_index >= len(s.cards):
            self._next_level()
        else:
            self._invalidate()

    def lv0_n(self):
        self._advance_card()
        self._invalidate()

    def lv0_j(self):
        s = self._state
        s.message = ""
        if not self._load_level(1):
            if not self._load_level(2):
                self._go_input()
                return
        self._invalidate()

    # ── PROCESS Lv1 ──────────────────────────────────────────────────────────

    def lv1_o(self):
        s = self._state
        card = s.current_card
        if card is None:
            return
        if not s.memos_available or self._memos is None:
            s.message = "Memos 無法連線，無法完成"
            self._advance_card()
            self._invalidate()
            return
        try:
            uid = self._memos.push(card.content)
            s.items = [i for i in s.items if i.id != card.id]
            self._save()
            s.cards = [c for c in s.cards if c.id != card.id]
            s.message = ""
            if s.card_index >= len(s.cards):
                self._next_level()
            else:
                self._invalidate()
        except MemosError as e:
            s.message = f"推送失敗，稍後重試"
            self._advance_card()
            self._invalidate()

    def lv1_x(self):
        s = self._state
        card = s.current_card
        if card is None:
            return
        s.items = [i for i in s.items if i.id != card.id]
        self._save()
        s.cards = [c for c in s.cards if c.id != card.id]
        if s.card_index >= len(s.cards):
            self._next_level()
        else:
            self._invalidate()

    def lv1_a(self):
        s = self._state
        card = s.current_card
        if card is None:
            return
        if s.pin_count >= 3:
            self._go_input("代辦三格已滿")
            return
        card.pinned = True
        self._save()
        self._advance_card()
        self._invalidate()

    def lv1_s(self):
        s = self._state
        s.mode = Mode.S_TAG
        s.input_buffer = ""
        s.message = ""
        self._invalidate()

    def lv1_n(self):
        self._advance_card()
        self._invalidate()

    def lv1_j(self):
        s = self._state
        s.message = ""
        if not self._load_level(2):
            self._go_input()
            return
        self._invalidate()

    # ── S_TAG ─────────────────────────────────────────────────────────────────

    def s_tag_enter(self):
        s = self._state
        card = s.current_card
        if card is None:
            s.mode = Mode.PROCESS
            self._invalidate()
            return
        raw_tag = s.input_buffer.strip()
        tag = raw_tag if raw_tag else card.content
        # strip any existing bracket prefix from content
        base_content = card.content
        if base_content.startswith("[") and "]" in base_content:
            base_content = base_content[base_content.index("]") + 1:]
        card.content = f"[{tag}]{base_content}"
        card.parent_tag = tag
        card.level = 2
        self._save()
        s.cards = [c for c in s.cards if c.id != card.id]
        s.input_buffer = ""
        s.mode = Mode.PROCESS
        if s.card_index >= len(s.cards):
            self._next_level()
        else:
            self._invalidate()

    # ── PROCESS Lv2 ──────────────────────────────────────────────────────────

    def lv2_c(self):
        s = self._state
        card = s.current_card
        if card is None:
            return
        s.cut_card = card
        s.mode = Mode.CUT
        s.input_buffer = ""
        s.message = ""
        self._invalidate()

    def lv2_u(self):
        s = self._state
        card = s.current_card
        if card is None:
            return
        card.level = 3
        self._save()
        s.cards = [c for c in s.cards if c.id != card.id]
        if s.card_index >= len(s.cards):
            self._next_level()
        else:
            self._invalidate()

    def lv2_n(self):
        self._advance_card()
        self._invalidate()

    # ── CUT ──────────────────────────────────────────────────────────────────

    def cut_enter(self):
        s = self._state
        text = s.input_buffer.strip()
        if not text:
            return
        if s.lv1_count >= 10:
            self._go_input("Lv1 已滿 10 格，請先處理")
            return
        cut = s.cut_card
        tag = cut.parent_tag if cut else ""
        content = f"[{tag}]{text}" if tag else text
        new_item = BujoItem(
            id=storage.next_id(s.items),
            content=content,
            level=1,
            parent_tag=tag,
            pinned=False,
            created_at=datetime.now(timezone.utc),
            memos_id="",
        )
        s.items.append(new_item)
        self._save()
        s.input_buffer = ""
        s.message = ""
        self._invalidate()

    def cut_x(self):
        s = self._state
        s.mode = Mode.PROCESS
        s.input_buffer = ""
        s.message = ""
        s.cut_card = None
        self._advance_card()
        self._invalidate()

    # ── Tab in PROCESS ────────────────────────────────────────────────────────

    def process_tab(self):
        self._go_input()


def build_app(config: Config, start_mode: Mode = Mode.INPUT) -> Application:
    items = storage.read_items(config.csv_path)

    memos: MemosClient | None = None
    memos_ok = False
    if config.memos_token:
        memos = MemosClient(config.memos_url, config.memos_token)
        memos_ok = memos.test_connection()

    state = AppState(
        items=items,
        mode=start_mode,
        memos_available=memos_ok,
    )

    if not memos_ok:
        if not config.memos_token:
            state.message = "Memos token 未設定，Lv1 完成功能停用"
        else:
            state.message = "Memos 無法連線，Lv1 完成功能停用"

    app_ref: list = [None]
    handlers = Handlers(state, config, memos, app_ref)

    if start_mode == Mode.PROCESS:
        if not state.cards_for_level(0) and not state.cards_for_level(1) and not state.cards_for_level(2):
            state.mode = Mode.INPUT
        else:
            handlers._load_level(0) or handlers._load_level(1) or handlers._load_level(2)
            state.mode = Mode.PROCESS

    layout = build_layout(state)
    kb = build_bindings(state, handlers)

    app = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=True,
        mouse_support=False,
    )
    app_ref[0] = app
    # expose state so flash.py can reach it without circular imports
    app._cthulhu_state = state  # type: ignore[attr-defined]

    from cthulhu_note import flash as flash_mod
    flash_mod.maybe_flash(state.items, config, app)

    return app
