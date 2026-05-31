from dataclasses import dataclass
from typing import Protocol

EXCEL_MAX_COLUMNS = 16384


@dataclass(frozen=True, slots=True)
class Rect:
    row: int
    col: int
    height: int
    width: int


class Allocator(Protocol):
    def alloc(self, height: int, width: int) -> Rect: ...
    def free(self, rect: Rect) -> None: ...


class ArenaAllocator:
    def __init__(
        self,
        start_row: int = 1,
        start_col: int = 1,
        max_width: int = EXCEL_MAX_COLUMNS,
        gap: int = 1,
    ) -> None:
        if start_row <= 0 or start_col <= 0:
            raise ValueError('start_row and start_col must be positive')
        if max_width < start_col:
            raise ValueError('max_width must be >= start_col')
        if max_width > EXCEL_MAX_COLUMNS:
            raise ValueError(f'max_width must be <= {EXCEL_MAX_COLUMNS}')
        if gap < 0:
            raise ValueError('gap must be non-negative')

        self._row = start_row
        self._col = start_col

        self._start_col = start_col
        self._max_width = max_width
        self._gap = gap

        self._current_row_height = 0

    def alloc(self, height: int, width: int) -> Rect:
        if height <= 0 or width <= 0:
            raise ValueError('height and width must be positive')

        available_width = self._max_width - self._start_col + 1
        if width > available_width:
            raise ValueError(
                f'width={width} exceeds available row width={available_width}'
            )

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

    def free(self, rect: Rect) -> None:
        # No-op for now since we don't reuse freed space.
        pass


__all__ = ['ArenaAllocator', 'Allocator', 'EXCEL_MAX_COLUMNS', 'Rect']
