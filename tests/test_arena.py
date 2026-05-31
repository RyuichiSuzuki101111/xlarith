"""Tests for arena-style placement allocation behavior."""

import unittest

from xlarith.allocator import EXCEL_MAX_COLUMNS, ArenaAllocator


class TestArena(unittest.TestCase):
    """Validate coordinate allocation and input validation in ArenaAllocator."""

    def test_default_max_width_matches_excel_limit(self) -> None:
        """Default width should match Excel's maximum column count."""
        arena = ArenaAllocator()
        self.assertEqual(arena._max_width, EXCEL_MAX_COLUMNS)

    def test_alloc_without_wrap(self) -> None:
        """Sequential allocations should stay on the same row when space remains."""
        arena = ArenaAllocator(start_row=1, start_col=1, max_width=10, gap=1)
        a = arena.alloc(2, 2)
        b = arena.alloc(1, 3)

        self.assertEqual((a.row, a.col, a.height, a.width), (1, 1, 2, 2))
        self.assertEqual((b.row, b.col, b.height, b.width), (1, 4, 1, 3))

    def test_alloc_wraps_when_exceeds_width(self) -> None:
        """Allocation should wrap to the next row block when width is exceeded."""
        arena = ArenaAllocator(start_row=1, start_col=1, max_width=5, gap=1)
        _ = arena.alloc(2, 3)
        wrapped = arena.alloc(1, 3)

        self.assertEqual((wrapped.row, wrapped.col), (4, 1))

    def test_alloc_rejects_non_positive(self) -> None:
        """Non-positive dimensions should raise a ValueError."""
        arena = ArenaAllocator()
        with self.assertRaises(ValueError):
            arena.alloc(0, 1)

    def test_init_rejects_invalid_bounds(self) -> None:
        """Invalid start/max-width combinations should be rejected."""
        with self.assertRaises(ValueError):
            ArenaAllocator(start_col=10, max_width=9)
        with self.assertRaises(ValueError):
            ArenaAllocator(max_width=EXCEL_MAX_COLUMNS + 1)

    def test_alloc_rejects_width_exceeding_row_capacity(self) -> None:
        """Requested width larger than remaining row capacity should fail."""
        arena = ArenaAllocator(start_col=3, max_width=5)
        with self.assertRaises(ValueError):
            arena.alloc(1, 4)


if __name__ == '__main__':
    unittest.main()
