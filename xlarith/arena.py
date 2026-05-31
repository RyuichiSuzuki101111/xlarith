from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Rect:
    row: int
    col: int
    height: int
    width: int


class Arena:
    def __init__(
        self,
        start_row: int = 1,
        start_col: int = 1,
        max_width: int = 256,
        gap: int = 1,
    ) -> None:
        self._row = start_row
        self._col = start_col

        self._start_col = start_col
        self._max_width = max_width
        self._gap = gap

        self._current_row_height = 0

    def alloc(self, height: int, width: int) -> Rect:
        if height <= 0 or width <= 0:
            raise ValueError('height and width must be positive')

        if self._col != self._start_col and self._col + width - 1 > self._max_width:
            self._row += self._current_row_height + self._gap
            self._col = self._start_col
            self._current_row_height = 0

        rect = Rect(
            row=self._row,
            col=self._col,
            height=height,
            width=width,
        )

        self._col += width + self._gap
        self._current_row_height = max(
            self._current_row_height,
            height,
        )

        return rect
