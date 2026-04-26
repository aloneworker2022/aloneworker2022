from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings

from cthulhu_note.state import AppState, Mode


def build_bindings(state: AppState, handlers) -> KeyBindings:
    kb = KeyBindings()

    is_input = Condition(lambda: state.mode == Mode.INPUT)
    is_process_lv0 = Condition(lambda: state.mode == Mode.PROCESS and state.process_level == 0)
    is_process_lv1 = Condition(lambda: state.mode == Mode.PROCESS and state.process_level == 1)
    is_process_lv2 = Condition(lambda: state.mode == Mode.PROCESS and state.process_level == 2)
    is_cut = Condition(lambda: state.mode == Mode.CUT)
    is_s_tag = Condition(lambda: state.mode == Mode.S_TAG)
    is_ctrl_v = Condition(lambda: state.mode == Mode.CTRL_V)
    is_flash = Condition(lambda: state.mode == Mode.FLASH)
    not_flash = Condition(lambda: state.mode != Mode.FLASH)

    # ── block everything during flash ────────────────────────────────────────
    @kb.add("<any>", filter=is_flash)
    def _flash_block(event):
        pass

    # ── INPUT mode ───────────────────────────────────────────────────────────
    @kb.add("enter", filter=is_input)
    def _input_enter(event):
        handlers.input_enter()

    @kb.add("tab", filter=is_input)
    def _input_tab(event):
        handlers.input_tab()

    @kb.add("c-v", filter=is_input)
    def _input_ctrl_v(event):
        handlers.ctrl_v_open()

    @kb.add("backspace", filter=is_input)
    def _input_backspace(event):
        handlers.input_backspace()

    @kb.add("<any>", filter=is_input)
    def _input_char(event):
        handlers.input_char(event.data)

    # ── PROCESS Lv0 ──────────────────────────────────────────────────────────
    @kb.add("o", filter=is_process_lv0)
    def _p0_o(event):
        handlers.lv0_o()

    @kb.add("x", filter=is_process_lv0)
    def _p0_x(event):
        handlers.lv0_x()

    @kb.add("n", filter=is_process_lv0)
    def _p0_n(event):
        handlers.lv0_n()

    @kb.add("j", filter=is_process_lv0)
    def _p0_j(event):
        handlers.lv0_j()

    @kb.add("tab", filter=is_process_lv0)
    def _p0_tab(event):
        handlers.process_tab()

    # ── PROCESS Lv1 ──────────────────────────────────────────────────────────
    @kb.add("o", filter=is_process_lv1)
    def _p1_o(event):
        handlers.lv1_o()

    @kb.add("x", filter=is_process_lv1)
    def _p1_x(event):
        handlers.lv1_x()

    @kb.add("a", filter=is_process_lv1)
    def _p1_a(event):
        handlers.lv1_a()

    @kb.add("s", filter=is_process_lv1)
    def _p1_s(event):
        handlers.lv1_s()

    @kb.add("n", filter=is_process_lv1)
    def _p1_n(event):
        handlers.lv1_n()

    @kb.add("j", filter=is_process_lv1)
    def _p1_j(event):
        handlers.lv1_j()

    @kb.add("tab", filter=is_process_lv1)
    def _p1_tab(event):
        handlers.process_tab()

    # ── PROCESS Lv2 ──────────────────────────────────────────────────────────
    @kb.add("o", filter=is_process_lv2)
    def _p2_o(event):
        handlers.lv2_o()

    @kb.add("c", filter=is_process_lv2)
    def _p2_c(event):
        handlers.lv2_c()

    @kb.add("u", filter=is_process_lv2)
    def _p2_u(event):
        handlers.lv2_u()

    @kb.add("n", filter=is_process_lv2)
    def _p2_n(event):
        handlers.lv2_n()

    @kb.add("tab", filter=is_process_lv2)
    def _p2_tab(event):
        handlers.process_tab()

    # ── CUT mode ─────────────────────────────────────────────────────────────
    @kb.add("enter", filter=is_cut)
    def _cut_enter(event):
        handlers.cut_enter()

    @kb.add("x", filter=is_cut)
    def _cut_x(event):
        handlers.cut_x()

    @kb.add("backspace", filter=is_cut)
    def _cut_backspace(event):
        handlers.input_backspace()

    @kb.add("<any>", filter=is_cut)
    def _cut_char(event):
        handlers.input_char(event.data)

    # ── S_TAG mode ───────────────────────────────────────────────────────────
    @kb.add("enter", filter=is_s_tag)
    def _stag_enter(event):
        handlers.s_tag_enter()

    @kb.add("backspace", filter=is_s_tag)
    def _stag_backspace(event):
        handlers.input_backspace()

    @kb.add("<any>", filter=is_s_tag)
    def _stag_char(event):
        handlers.input_char(event.data)

    # ── CTRL_V mode ──────────────────────────────────────────────────────────
    @kb.add("up", filter=is_ctrl_v)
    @kb.add("k", filter=is_ctrl_v)
    def _cv_up(event):
        handlers.ctrl_v_move(-1)

    @kb.add("down", filter=is_ctrl_v)
    @kb.add("j", filter=is_ctrl_v)
    def _cv_down(event):
        handlers.ctrl_v_move(1)

    @kb.add("enter", filter=is_ctrl_v)
    def _cv_enter(event):
        handlers.ctrl_v_enter()

    @kb.add("escape", filter=is_ctrl_v)
    def _cv_esc(event):
        handlers.ctrl_v_close()

    # ── global quit ──────────────────────────────────────────────────────────
    @kb.add("c-c", filter=not_flash)
    @kb.add("c-q", filter=not_flash)
    def _quit(event):
        event.app.exit()

    return kb
