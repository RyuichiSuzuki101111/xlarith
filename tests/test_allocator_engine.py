"""Tests for engine helper behavior and evaluator result normalization."""

import unittest

from xlarith.engine import Engine
from xlarith.evaluator import Evaluator
from xlarith.term import Ref


class TestEngineHelpers(unittest.TestCase):
    """Verify Engine helper methods and compile-time validation."""

    def test_create_ref_stores_shape(self) -> None:
        """create_ref should persist shape metadata and register the reference."""
        engine = Engine()

        ref = engine.create_ref([[1, 2], [3, 4]])

        self.assertEqual(ref.shape, (2, 2))
        self.assertEqual(ref.key, 1)
        self.assertIn(ref, engine._bound_values)

    def test_collect_refs_deduplicates_and_keeps_order(self) -> None:
        """Reference collection should keep first-seen order and remove duplicates."""
        engine = Engine()
        a = Ref(key=1, shape=(1, 1))
        b = Ref(key=2, shape=(1, 1))
        expr = (a + b) + a

        refs = Engine._collect_refs(engine, expr)

        self.assertEqual(refs, [a, b])

    def test_compile_validates_references(self) -> None:
        """Compile should reject references not created by the engine instance."""
        engine = Engine()
        created = engine.create_ref(1)
        foreign = Ref(key=999, shape=(1, 1))

        compiled = engine.compile(created + 2)
        self.assertEqual(compiled.refs, (created,))
        self.assertEqual(compiled.output_shape, (1, 1))

        with self.assertRaises(ValueError):
            engine.compile(foreign + 1)

    def test_compile_collects_materialized_terms(self) -> None:
        """Compile should track materialized nodes in evaluation order."""
        engine = Engine()
        a = engine.create_ref(1)
        b = engine.create_ref(2)
        partial = engine.materialize(a + b)

        compiled = engine.compile(partial + 3)

        self.assertEqual(compiled.refs, (a, b))
        self.assertEqual(compiled.materialized, (partial,))
        self.assertEqual(compiled.output_shape, (1, 1))

    def test_evaluate_requires_allocator_configuration(self) -> None:
        """Evaluate should fail until an allocator-backed evaluator is configured."""
        engine = Engine()
        x = engine.create_ref(1)

        with self.assertRaises(RuntimeError):
            engine.evaluate(x + 1)


class TestEvaluatorHelpers(unittest.TestCase):
    """Verify shape-aware normalization of Excel evaluation results."""

    def test_normalize_result_shapes(self) -> None:
        """List/2D results should normalize according to expected output shape."""
        evaluator = Evaluator.__new__(Evaluator)

        self.assertEqual(Evaluator._normalize_result(evaluator, 10, (1, 1)), 10)
        self.assertEqual(
            Evaluator._normalize_result(evaluator, [1, 2, 3], (1, 3)),
            [1, 2, 3],
        )
        self.assertEqual(
            Evaluator._normalize_result(evaluator, [1, 2], (2, 1)),
            [1, 2],
        )
        self.assertEqual(
            Evaluator._normalize_result(evaluator, [[1, 2], [3, 4]], (2, 2)),
            [[1, 2], [3, 4]],
        )

    def test_normalize_result_handles_tuple_sequences(self) -> None:
        """Tuple-based Excel results should normalize like list-based results."""
        evaluator = Evaluator.__new__(Evaluator)

        self.assertEqual(
            Evaluator._normalize_result(evaluator, ((1, 2, 3),), (1, 3)),
            [1, 2, 3],
        )
        self.assertEqual(
            Evaluator._normalize_result(evaluator, ((1,), (2,)), (2, 1)),
            [1, 2],
        )
        self.assertEqual(
            Evaluator._normalize_result(evaluator, ((1, 2), (3, 4)), (2, 2)),
            [[1, 2], [3, 4]],
        )


if __name__ == '__main__':
    unittest.main()
