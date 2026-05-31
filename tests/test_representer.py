import unittest

from xlarith.representer import ExcelRepresenter
from xlarith.term import Materialized, Ref, WorksheetFunctions, term_shape, to_term


class TestExcelRepresenter(unittest.TestCase):
    def test_represent_binary_expression(self) -> None:
        a = Ref(key=1, shape=(1, 1))
        b = Ref(key=2, shape=(1, 1))
        representer = ExcelRepresenter({a: 'A1', b: 'B1'})
        formula_body = representer.represent_root(a + b)
        self.assertEqual(formula_body, '(A1+B1)')

    def test_represent_array_constant(self) -> None:
        representer = ExcelRepresenter({})
        term = to_term([[1, 2], [3, 4]])
        self.assertEqual(representer.represent_root(term), '{1,2;3,4}')

    def test_represent_unary_function(self) -> None:
        a = Ref(key=1, shape=(1, 1))
        representer = ExcelRepresenter({a: 'C3'})
        formula_body = representer.represent_root(WorksheetFunctions.abs(a))
        self.assertEqual(formula_body, 'ABS(C3)')

    def test_represent_materialized_term_as_address(self) -> None:
        a = Ref(key=1, shape=(1, 1))
        b = Ref(key=2, shape=(1, 1))
        partial_expr = a + b
        partial = Materialized(partial_expr, term_shape(partial_expr))
        representer = ExcelRepresenter({a: 'A1', b: 'A2', partial: 'B1'})
        formula_body = representer.represent_root(partial + 3)
        self.assertEqual(formula_body, '(B1+3)')

    def test_represent_root_materialized_as_value_expression(self) -> None:
        a = Ref(key=1, shape=(1, 1))
        b = Ref(key=2, shape=(1, 1))
        partial_expr = a + b
        partial = Materialized(partial_expr, term_shape(partial_expr))
        representer = ExcelRepresenter({a: 'A1', b: 'A2', partial: 'B1'})
        formula_body = representer.represent_root(partial)
        self.assertEqual(formula_body, '(A1+A2)')

    def test_represent_array_constant_escapes_text(self) -> None:
        representer = ExcelRepresenter({})
        term = to_term([['a"b', 'x']])
        self.assertEqual(representer.represent_root(term), '{"a""b","x"}')

    def test_represent_array_constant_keeps_numeric_text_unquoted(self) -> None:
        representer = ExcelRepresenter({})
        term = to_term([['1.5', '-2']])
        self.assertEqual(representer.represent_root(term), '{1.5,-2}')

    def test_represent_ref_raises_when_not_placed(self) -> None:
        a = Ref(key=1, shape=(1, 1))
        representer = ExcelRepresenter({})
        with self.assertRaises(ValueError):
            representer.represent_root(a)


if __name__ == '__main__':
    unittest.main()
