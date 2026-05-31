import unittest

from xlarith.allocator import Engine
from xlarith.term import Ref


class TestEngineHelpers(unittest.TestCase):
    def test_create_ref_stores_shape(self) -> None:
        engine = Engine.__new__(Engine)
        engine._next_ref_key = 1
        engine._bound_values = {}

        ref = Engine.create_ref(engine, [[1, 2], [3, 4]])

        self.assertEqual(ref.shape, (2, 2))
        self.assertEqual(ref.key, 1)
        self.assertIn(ref, engine._bound_values)

    def test_collect_refs_deduplicates_and_keeps_order(self) -> None:
        engine = Engine.__new__(Engine)
        a = Ref(key=1, shape=(1, 1))
        b = Ref(key=2, shape=(1, 1))
        expr = (a + b) + a

        refs = Engine._collect_refs(engine, expr)

        self.assertEqual(refs, [a, b])

    def test_normalize_result_shapes(self) -> None:
        engine = Engine.__new__(Engine)

        self.assertEqual(Engine._normalize_result(engine, 10, (1, 1)), 10)
        self.assertEqual(Engine._normalize_result(engine, [1, 2, 3], (1, 3)), [1, 2, 3])
        self.assertEqual(Engine._normalize_result(engine, [1, 2], (2, 1)), [1, 2])
        self.assertEqual(
            Engine._normalize_result(engine, [[1, 2], [3, 4]], (2, 2)),
            [[1, 2], [3, 4]],
        )


if __name__ == '__main__':
    unittest.main()
