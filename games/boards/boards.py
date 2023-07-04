from dataclasses import InitVar, dataclass, field
from typing import Optional, Sequence


@dataclass
class Piece:
    icon: str

    def __str__(self):
        return self.icon


@dataclass
class Cell:
    base_emoji: str
    piece: Optional[Piece] = None

    def __str__(self):
        return str(self.piece) or self.base_emoji


@dataclass
class Row:
    emojis: InitVar[Sequence[str]]
    column_count: InitVar[int]
    cells: list[Cell] = field(default_factory=list)

    def __str__(self):
        return "".join(str(c) for c in self.cells)

    def __post_init__(self, emojis: Sequence[str], column_count: int):
        emoji_count = len(emojis)
        emoji_index = 0
        for column_number in range(column_count):
            self.cells.append(Cell(emojis[emoji_index], ""))
            emoji_index = (emoji_index + 1) % emoji_count


@dataclass
class Board:
    width: int
    height: int
    primary_emoji: str = "⬜"
    secondary_emoji: str | None = "🟩"
    checked: bool = False
    rows: list[Row] = field(default_factory=list)

    def __post_init__(self):
        if self.checked and not self.secondary_emoji:
            raise ValueError("If the board is checked, you must provide a secondary emoji.")
        emojis = (self.primary_emoji, self.secondary_emoji) if self.checked else (self.primary_emoji,)
        for row_number in range(self.height):
            self.rows.append(Row(emojis, self.height))
            emojis = emojis[::-1] if self.checked else emojis
        self.initialise_game()

    def initialise_game(self):
        pass

    def __str__(self):
        return "\n".join(str(row) for row in self.rows)


class CheckersBoard(Board):
    def initialise_game(self):
        for i in range(2):
            for cell_index in range((i + 1) % 2, len(self.rows[i].cells), 2):
                self.rows[i].cells[cell_index].piece = Piece("🔴")
        for i in range(1, 3):
            for cell_index in range((i + 1) % 2, len(self.rows[len(self.rows) - i].cells), 2):
                self.rows[len(self.rows) - i].cells[cell_index].piece = Piece("🔵")
