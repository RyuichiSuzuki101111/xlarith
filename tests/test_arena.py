import unittest

from xlarith.allocator import EXCEL_MAX_COLUMNS, ArenaAllocator


class TestArena(unittest.TestCase):
    def test_default_max_width_matches_excel_limit(self) -> None:
        arena = ArenaAllocator()
        self.assertEqual(arena._max_width, EXCEL_MAX_COLUMNS)

    def test_alloc_without_wrap(self) -> None:
        arena = ArenaAllocator(start_row=1, start_col=1, max_width=10, gap=1)
        a = arena.alloc(2, 2)
        b = arena.alloc(1, 3)

        self.assertEqual((a.row, a.col, a.height, a.width), (1, 1, 2, 2))
        self.assertEqual((b.row, b.col, b.height, b.width), (1, 4, 1, 3))

    def test_alloc_wraps_when_exceeds_width(self) -> None:
        arena = ArenaAllocator(start_row=1, start_col=1, max_width=5, gap=1)
        _ = arena.alloc(2, 3)
        wrapped = arena.alloc(1, 3)

        self.assertEqual((wrapped.row, wrapped.col), (4, 1))

    def test_alloc_rejects_non_positive(self) -> None:
        arena = ArenaAllocator()
        with self.assertRaises(ValueError):
            arena.alloc(0, 1)

    def test_init_rejects_invalid_bounds(self) -> None:
        with self.assertRaises(ValueError):
            ArenaAllocator(start_col=10, max_width=9)
        with self.assertRaises(ValueError):
            ArenaAllocator(max_width=EXCEL_MAX_COLUMNS + 1)

    def test_alloc_rejects_width_exceeding_row_capacity(self) -> None:
        arena = ArenaAllocator(start_col=3, max_width=5)
        with self.assertRaises(ValueError):
            arena.alloc(1, 4)


if __name__ == '__main__':
    unittest.main()
