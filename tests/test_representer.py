import unittest

from xlarith.representer import ExcelRepresenter
from xlarith.term import Ref, to_term
from xlarith.term import abs as xabs


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
        formula_body = representer.represent_root(xabs(a))
        self.assertEqual(formula_body, 'ABS(C3)')


if __name__ == '__main__':
    unittest.main()
