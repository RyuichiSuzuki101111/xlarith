import unittest

from xlarith.term import (
    BinaryOp,
    Constant,
    OperatorTag,
    Ref,
    broadcast_shape,
    normalize_excel_value,
    term_shape,
    to_term,
)


class TestNormalizeExcelValue(unittest.TestCase):
    def test_scalar(self) -> None:
        self.assertEqual(normalize_excel_value(3.5), ((3.5,),))

    def test_vector(self) -> None:
        self.assertEqual(normalize_excel_value([1, 2, 3]), ((1, 2, 3),))

    def test_matrix(self) -> None:
        self.assertEqual(normalize_excel_value([[1, 2], [3, 4]]), ((1, 2), (3, 4)))

    def test_reject_empty(self) -> None:
        with self.assertRaises(ValueError):
            normalize_excel_value([])


class TestBroadcastShape(unittest.TestCase):
    def test_broadcast_row_and_col(self) -> None:
        self.assertEqual(broadcast_shape((1, 3), (2, 1)), (2, 3))

    def test_reject_incompatible(self) -> None:
        with self.assertRaises(ValueError):
            broadcast_shape((2, 2), (3, 2))


class TestTermOps(unittest.TestCase):
    def test_python_operator_builds_binary_op(self) -> None:
        a = to_term(1)
        expr = a + 2
        self.assertIsInstance(expr, BinaryOp)
        self.assertEqual(expr.tag, OperatorTag.ADD)
        self.assertIsInstance(expr.left, Constant)
        self.assertIsInstance(expr.right, Constant)

    def test_term_shape_with_broadcast(self) -> None:
        a = Ref(key=1, shape=(1, 3))
        b = Ref(key=2, shape=(2, 1))
        self.assertEqual(term_shape(a + b), (2, 3))


if __name__ == '__main__':
    unittest.main()
