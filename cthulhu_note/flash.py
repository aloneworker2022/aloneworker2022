import random

from cthulhu_note.config import Config
from cthulhu_note.models import BujoItem
from cthulhu_note.state import Mode


def maybe_flash(items: list[BujoItem], config: Config, app) -> None:
    if not config.lv3_flash_enabled:
        return
    lv3 = [i for i in items if i.level == 3]
    if not lv3:
        return
    if random.random() >= config.lv3_flash_probability:
        return
    item = random.choice(lv3)
    _trigger_flash(item, config.lv3_flash_duration, app)


def _trigger_flash(item: BujoItem, duration: float, app) -> None:
    from cthulhu_note.app import Handlers  # avoid circular at module level
    state = _get_state(app)
    if state is None:
        return

    prev_mode = state.mode
    state.flash_content = item.content
    state.mode = Mode.FLASH
    app.invalidate()

    import asyncio

    def _end():
        state.mode = prev_mode
        state.flash_content = ""
        app.invalidate()

    loop = asyncio.get_event_loop()
    loop.call_later(duration, _end)


def _get_state(app):
    try:
        # The state is stored in the layout's controls via closures.
        # We retrieve it from the app's key_bindings handler closure.
        # Simpler: store a reference on the app object itself.
        return app._cthulhu_state
    except AttributeError:
        return None
