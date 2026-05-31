import unittest

from xlarith.arena import Arena


class TestArena(unittest.TestCase):
    def test_alloc_without_wrap(self) -> None:
        arena = Arena(start_row=1, start_col=1, max_width=10, gap=1)
        a = arena.alloc(2, 2)
        b = arena.alloc(1, 3)

        self.assertEqual((a.row, a.col, a.height, a.width), (1, 1, 2, 2))
        self.assertEqual((b.row, b.col, b.height, b.width), (1, 4, 1, 3))

    def test_alloc_wraps_when_exceeds_width(self) -> None:
        arena = Arena(start_row=1, start_col=1, max_width=5, gap=1)
        _ = arena.alloc(2, 3)
        wrapped = arena.alloc(1, 3)

        self.assertEqual((wrapped.row, wrapped.col), (4, 1))

    def test_alloc_rejects_non_positive(self) -> None:
        arena = Arena()
        with self.assertRaises(ValueError):
            arena.alloc(0, 1)


if __name__ == '__main__':
    unittest.main()
