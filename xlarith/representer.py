from __future__ import annotations

from .term import (
    ArrayConstant,
    BinaryOp,
    Constant,
    Notation,
    OperatorTag,
    Ref,
    TermBase,
    UnaryOp,
)


def _looks_numeric(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def _format_scalar(value: int | float | str) -> str:
    if isinstance(value, int | float):
        return str(value)

    if _looks_numeric(value):
        return value

    escaped = value.replace('"', '""')
    return f'"{escaped}"'


class ExcelRepresenter:
    def __init__(self, ref_addresses: dict[Ref, str]) -> None:
        self._ref_addresses = ref_addresses

    def represent_root(self, term: TermBase) -> str:
        return self.represent(term)

    def represent(self, term: TermBase) -> str:
        if isinstance(term, Constant):
            return term.expr

        if isinstance(term, ArrayConstant):
            return self._array_constant(term)

        if isinstance(term, Ref):
            if term not in self._ref_addresses:
                raise ValueError(f'Reference key={term.key} was not placed in arena.')
            return self._ref_addresses[term]

        if isinstance(term, UnaryOp):
            inner = self.represent(term.term)
            if term.tag.notation is Notation.PREFIX:
                return f'({term.tag.symbol}{inner})'
            return f'{self._excel_function_name(term.tag)}({inner})'

        if isinstance(term, BinaryOp):
            left = self.represent(term.left)
            right = self.represent(term.right)
            if term.tag.notation is Notation.INFIX:
                return f'({left}{term.tag.symbol}{right})'
            return f'{self._excel_function_name(term.tag)}({left},{right})'

        raise TypeError(f'Unsupported term type: {type(term)}')

    def _array_constant(self, term: ArrayConstant) -> str:
        row_exprs: list[str] = []
        for row in term.matrix:
            row_expr = ','.join(_format_scalar(v) for v in row)
            row_exprs.append(row_expr)
        return '{' + ';'.join(row_exprs) + '}'

    def _excel_function_name(self, tag: OperatorTag) -> str:
        names = {
            OperatorTag.ABS: 'ABS',
            OperatorTag.SQRT: 'SQRT',
            OperatorTag.LOG10: 'LOG10',
            OperatorTag.LOG: 'LN',
            OperatorTag.ROUND: 'ROUND',
            OperatorTag.SUM: 'SUM',
            OperatorTag.PRODUCT: 'PRODUCT',
        }
        if tag not in names:
            raise ValueError(f'No Excel function mapping for {tag.name}')
        return names[tag]


__all__ = ['ExcelRepresenter']
