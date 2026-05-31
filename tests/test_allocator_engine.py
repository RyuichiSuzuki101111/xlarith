import unittest

from xlarith.allocator import DefaultAllocator
from xlarith.engine import Engine
from xlarith.term import Ref


class TestEngineHelpers(unittest.TestCase):
    def test_create_ref_stores_shape(self) -> None:
        engine = Engine()

        ref = engine.create_ref([[1, 2], [3, 4]])

        self.assertEqual(ref.shape, (2, 2))
        self.assertEqual(ref.key, 1)
        self.assertIn(ref, engine._bound_values)

    def test_collect_refs_deduplicates_and_keeps_order(self) -> None:
        engine = Engine()
        a = Ref(key=1, shape=(1, 1))
        b = Ref(key=2, shape=(1, 1))
        expr = (a + b) + a

        refs = Engine._collect_refs(engine, expr)

        self.assertEqual(refs, [a, b])

    def test_compile_validates_references(self) -> None:
        engine = Engine()
        created = engine.create_ref(1)
        foreign = Ref(key=999, shape=(1, 1))

        compiled = engine.compile(created + 2)
        self.assertEqual(compiled.refs, (created,))
        self.assertEqual(compiled.output_shape, (1, 1))

        with self.assertRaises(ValueError):
            engine.compile(foreign + 1)

    def test_evaluate_requires_allocator_configuration(self) -> None:
        engine = Engine()
        x = engine.create_ref(1)

        with self.assertRaises(RuntimeError):
            engine.evaluate(x + 1)


class TestAllocatorHelpers(unittest.TestCase):
    def test_normalize_result_shapes(self) -> None:
        allocator = DefaultAllocator.__new__(DefaultAllocator)

        self.assertEqual(DefaultAllocator._normalize_result(allocator, 10, (1, 1)), 10)
        self.assertEqual(
            DefaultAllocator._normalize_result(allocator, [1, 2, 3], (1, 3)),
            [1, 2, 3],
        )
        self.assertEqual(
            DefaultAllocator._normalize_result(allocator, [1, 2], (2, 1)),
            [1, 2],
        )
        self.assertEqual(
            DefaultAllocator._normalize_result(allocator, [[1, 2], [3, 4]], (2, 2)),
            [[1, 2], [3, 4]],
        )

    def test_normalize_result_handles_tuple_sequences(self) -> None:
        allocator = DefaultAllocator.__new__(DefaultAllocator)

        self.assertEqual(
            DefaultAllocator._normalize_result(allocator, ((1, 2, 3),), (1, 3)),
            [1, 2, 3],
        )
        self.assertEqual(
            DefaultAllocator._normalize_result(allocator, ((1,), (2,)), (2, 1)),
            [1, 2],
        )
        self.assertEqual(
            DefaultAllocator._normalize_result(allocator, ((1, 2), (3, 4)), (2, 2)),
            [[1, 2], [3, 4]],
        )


if __name__ == '__main__':
    unittest.main()
