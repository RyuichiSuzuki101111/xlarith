from __future__ import annotations

from .term import (
    ArrayConstant,
    BinaryOp,
    Constant,
    Materialized,
    Notation,
    OperatorTag,
    Ref,
    TermBase,
    UnaryOp,
)


def _looks_numeric(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    else:
        return True


def _format_scalar(value: float | str) -> str:
    if isinstance(value, int | float):
        return str(value)

    if _looks_numeric(value):
        return value

    escaped = value.replace('"', '""')
    return f'"{escaped}"'


class ExcelRepresenter:
    def __init__(self, ref_addresses: dict[Ref | Materialized, str]) -> None:
        self._ref_addresses = ref_addresses

    def represent_root(self, term: TermBase) -> str:
        # Root terms are rendered as value expressions for the output cell.
        return self._represent(term, as_subexpression=False)

    def represent(self, term: TermBase) -> str:
        return self._represent(term, as_subexpression=True)

    def _represent(self, term: TermBase, *, as_subexpression: bool) -> str:
        if isinstance(term, Constant):
            return term.expr

        if isinstance(term, ArrayConstant):
            return self._array_constant(term)

        if isinstance(term, Materialized):
            if as_subexpression:
                if term not in self._ref_addresses:
                    msg = f'Term {term} was not placed in allocator.'
                    raise ValueError(msg)
                return self._ref_addresses[term]
            return self._represent(term.term, as_subexpression=True)

        if isinstance(term, Ref):
            if term not in self._ref_addresses:
                msg = f'Term {term} was not placed in allocator.'
                raise ValueError(msg)
            return self._ref_addresses[term]

        if isinstance(term, UnaryOp):
            inner = self._represent(term.term, as_subexpression=True)
            if term.tag.notation is Notation.PREFIX:
                return f'({term.tag.symbol}{inner})'
            return f'{self._excel_function_name(term.tag)}({inner})'

        if isinstance(term, BinaryOp):
            left = self._represent(term.left, as_subexpression=True)
            right = self._represent(term.right, as_subexpression=True)
            if term.tag.notation is Notation.INFIX:
                return f'({left}{term.tag.symbol}{right})'
            return f'{self._excel_function_name(term.tag)}({left},{right})'

        msg = f'Unsupported term type: {type(term)}'
        raise TypeError(msg)

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
            msg = f'No Excel function mapping for {tag.name}'
            raise ValueError(msg)
        return names[tag]


__all__ = ['ExcelRepresenter']
