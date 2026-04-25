from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    HSplit,
    Window,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.filters import Condition

from cthulhu_note.state import AppState, Mode

PIN_LIMIT = 3

# ── helpers ──────────────────────────────────────────────────────────────────


def _prompt_color(state: AppState) -> str:
    if state.mode == Mode.INPUT:
        return "ansigreen"
    if state.mode in (Mode.PROCESS, Mode.CUT):
        return "ansiyellow" if state.mode == Mode.PROCESS else "ansired"
    if state.mode == Mode.S_TAG:
        return "ansicyan"
    if state.mode == Mode.CTRL_V:
        return "ansigreen"
    return "ansiwhite"


def _prompt_label(state: AppState) -> str:
    if state.mode == Mode.INPUT:
        return "[加]:"
    if state.mode == Mode.PROCESS:
        lv = state.process_level
        return f"[處 Lv{lv}]:"
    if state.mode == Mode.CUT:
        return "[切]:"
    if state.mode == Mode.S_TAG:
        return "[??]:"
    if state.mode == Mode.CTRL_V:
        return "[代辦]:"
    return "[?]:"


def _hints(state: AppState) -> str:
    if state.mode == Mode.INPUT:
        return "Enter 加項目  Tab 切處理  Ctrl+V 代辦"
    if state.mode == Mode.PROCESS:
        lv = state.process_level
        if lv == 0:
            return "o升Lv1  x丟  n下  j跳Lv1  Tab中斷"
        if lv == 1:
            return "o完成  x丟  a釘  s想  n下  j跳Lv2  Tab中斷"
        if lv == 2:
            return "c切  u虛空  n下  Tab中斷"
    if state.mode == Mode.CUT:
        return "Enter送出切片  x離開"
    if state.mode == Mode.S_TAG:
        return "Enter確認標籤（空=用原內容）"
    if state.mode == Mode.CTRL_V:
        return "↑↓移動  Enter完成  Esc取消"
    return ""


# ── content builders ─────────────────────────────────────────────────────────


def make_header_text(state: AppState):
    pins = state.pinned_items
    lines = []
    for i in range(PIN_LIMIT):
        if i < len(pins):
            lines.append(("ansiblue bold", f"# {pins[i].content}\n"))
        else:
            lines.append(("ansiblue", "# ___\n"))
    return FormattedText(lines)


def make_body_text(state: AppState):
    if state.mode == Mode.FLASH:
        content = state.flash_content
        padding = "\n" * 4
        return FormattedText([
            ("", padding),
            ("ansigray italic", f"         ...{content}..."),
            ("", "\n"),
        ])

    if state.mode == Mode.CTRL_V:
        pins = state.pinned_items
        if not pins:
            return FormattedText([("ansigray", "\n  （代辦三格空空的）\n")])
        lines: list = [("", "\n")]
        for i, item in enumerate(pins):
            cursor = "> " if i == state.ctrl_v_cursor else "  "
            lines.append(("ansiyellow bold" if i == state.ctrl_v_cursor else "", f"{cursor}{item.content}\n"))
        return FormattedText(lines)

    if state.mode in (Mode.PROCESS, Mode.CUT, Mode.S_TAG):
        card = state.current_card
        if card:
            lv_tag = f"Lv{card.level}"
            return FormattedText([
                ("", "\n\n"),
                ("ansigray", f"  [{lv_tag}]\n"),
                ("bold", f"  {card.content}\n"),
                ("", "\n"),
            ])
        return FormattedText([("ansigray", "\n\n  （無卡片）\n\n")])

    # INPUT mode
    return FormattedText([("", "\n\n\n\n")])


def make_footer_text(state: AppState):
    color = _prompt_color(state)
    label = _prompt_label(state)
    buf = state.input_buffer
    msg = state.message
    hints = _hints(state)

    parts: list = []
    if msg:
        parts.append(("ansired", f"{msg}\n"))
    parts.append((f"{color} bold", label))
    parts.append(("", f" {buf}▮\n"))
    parts.append(("ansigray", hints))
    return FormattedText(parts)


# ── layout factory ────────────────────────────────────────────────────────────


def build_layout(state: AppState) -> Layout:
    header = Window(
        content=FormattedTextControl(lambda: make_header_text(state)),
        height=PIN_LIMIT,
    )
    sep_top = Window(height=1, char="─")
    body = Window(
        content=FormattedTextControl(lambda: make_body_text(state)),
    )
    sep_bot = Window(height=1, char="─")
    footer = Window(
        content=FormattedTextControl(lambda: make_footer_text(state)),
        height=4,
    )

    root = HSplit([header, sep_top, body, sep_bot, footer])
    return Layout(root)
