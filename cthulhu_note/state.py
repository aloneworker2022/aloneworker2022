from dataclasses import dataclass, field
from enum import Enum

from cthulhu_note.models import BujoItem


class Mode(Enum):
    INPUT = "input"
    PROCESS = "process"
    CUT = "cut"
    S_TAG = "s_tag"
    CTRL_V = "ctrl_v"
    FLASH = "flash"


@dataclass
class AppState:
    mode: Mode = Mode.INPUT
    process_level: int = 0
    cards: list[BujoItem] = field(default_factory=list)
    card_index: int = 0
    items: list[BujoItem] = field(default_factory=list)
    message: str = ""
    input_buffer: str = ""
    ctrl_v_cursor: int = 0
    flash_content: str = ""
    memos_available: bool = True

    # reference to the Lv2 card being cut from
    cut_card: BujoItem | None = None

    @property
    def current_card(self) -> BujoItem | None:
        if 0 <= self.card_index < len(self.cards):
            return self.cards[self.card_index]
        return None

    @property
    def lv1_count(self) -> int:
        return sum(1 for i in self.items if i.level == 1)

    @property
    def pin_count(self) -> int:
        return sum(1 for i in self.items if i.level == 1 and i.pinned)

    @property
    def pinned_items(self) -> list[BujoItem]:
        return [i for i in self.items if i.level == 1 and i.pinned]

    def cards_for_level(self, level: int) -> list[BujoItem]:
        return [i for i in self.items if i.level == level and not i.pinned]
