from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol, TypeAlias, TypeGuard

ExcelScalar: TypeAlias = int | float | str
ExcelArray1D: TypeAlias = Sequence[ExcelScalar]
ExcelArray2D: TypeAlias = Sequence[Sequence[ExcelScalar]]
ExcelValue: TypeAlias = ExcelScalar | ExcelArray1D | ExcelArray2D
TermLike: TypeAlias = ExcelValue | 'TermBase'
Shape: TypeAlias = tuple[int, int]
MatrixValue: TypeAlias = tuple[tuple[ExcelScalar, ...], ...]


class Representer(Protocol):
    def represent_root(self, term: TermBase) -> str: ...

    def represent(self, term: TermBase) -> str: ...


def _is_scalar(value: object) -> TypeGuard[ExcelScalar]:
    return isinstance(value, int | float | str)


def _is_sequence(value: object) -> TypeGuard[Sequence[object]]:
    return isinstance(value, Sequence) and not isinstance(
        value, str | bytes | bytearray
    )


def normalize_excel_value(value: ExcelValue) -> MatrixValue:
    if _is_scalar(value):
        return ((value,),)

    if not _is_sequence(value) or len(value) == 0:
        raise ValueError('Empty vectors/matrices are not supported.')

    first = value[0]
    if _is_sequence(first):
        rows: list[tuple[ExcelScalar, ...]] = []
        width = len(first)
        if width == 0:
            raise ValueError('Empty rows in matrices are not supported.')

        for row in value:
            if not _is_sequence(row):
                raise ValueError('Mixed vector/matrix inputs are not supported.')
            if len(row) != width:
                raise ValueError('Matrix rows must have the same length.')

            casted_row: list[ExcelScalar] = []
            for item in row:
                if not _is_scalar(item):
                    raise ValueError(
                        f'Unsupported element type in matrix: {type(item)}'
                    )
                casted_row.append(item)
            rows.append(tuple(casted_row))

        return tuple(rows)

    vector: list[ExcelScalar] = []
    for item in value:
        if not _is_scalar(item):
            raise ValueError(f'Unsupported element type in vector: {type(item)}')
        vector.append(item)

    return (tuple(vector),)


def shape_of_matrix(matrix: MatrixValue) -> Shape:
    return (len(matrix), len(matrix[0]))


def broadcast_shape(left: Shape, right: Shape) -> Shape:
    l_rows, l_cols = left
    r_rows, r_cols = right

    if l_rows != r_rows and l_rows != 1 and r_rows != 1:
        raise ValueError(f'Cannot broadcast row dimensions: {left} and {right}')
    if l_cols != r_cols and l_cols != 1 and r_cols != 1:
        raise ValueError(f'Cannot broadcast column dimensions: {left} and {right}')

    return (max(l_rows, r_rows), max(l_cols, r_cols))


class Notation(Enum):
    INFIX = auto()
    PREFIX = auto()
    FUNCTION = auto()


class OperatorTag(Enum):
    ADD = 'ADD'
    SUB = 'SUB'
    MUL = 'MUL'
    DIV = 'DIV'
    POW = 'POW'

    NEG = 'NEG'
    ABS = 'ABS'
    SQRT = 'SQRT'
    LOG10 = 'LOG10'
    LOG = 'LOG'
    ROUND = 'ROUND'
    SUM = 'SUM'
    PRODUCT = 'PRODUCT'

    @property
    def notation(self) -> Notation:
        if self in {
            OperatorTag.ADD,
            OperatorTag.SUB,
            OperatorTag.MUL,
            OperatorTag.DIV,
            OperatorTag.POW,
        }:
            return Notation.INFIX
        if self in {OperatorTag.NEG}:
            return Notation.PREFIX
        return Notation.FUNCTION

    @property
    def symbol(self) -> str:
        symbols = {
            OperatorTag.ADD: '+',
            OperatorTag.SUB: '-',
            OperatorTag.MUL: '*',
            OperatorTag.DIV: '/',
            OperatorTag.POW: '^',
            OperatorTag.NEG: '-',
        }
        if self not in symbols:
            raise ValueError(f'Operator {self.name} does not have infix/prefix symbol.')
        return symbols[self]


class TermBase:
    def __add__(self, other: TermLike) -> BinaryOp:
        return BinaryOp(OperatorTag.ADD, self, to_term(other))

    def __radd__(self, other: TermLike) -> BinaryOp:
        return BinaryOp(OperatorTag.ADD, to_term(other), self)

    def __sub__(self, other: TermLike) -> BinaryOp:
        return BinaryOp(OperatorTag.SUB, self, to_term(other))

    def __rsub__(self, other: TermLike) -> BinaryOp:
        return BinaryOp(OperatorTag.SUB, to_term(other), self)

    def __mul__(self, other: TermLike) -> BinaryOp:
        return BinaryOp(OperatorTag.MUL, self, to_term(other))

    def __rmul__(self, other: TermLike) -> BinaryOp:
        return BinaryOp(OperatorTag.MUL, to_term(other), self)

    def __truediv__(self, other: TermLike) -> BinaryOp:
        return BinaryOp(OperatorTag.DIV, self, to_term(other))

    def __rtruediv__(self, other: TermLike) -> BinaryOp:
        return BinaryOp(OperatorTag.DIV, to_term(other), self)

    def __pow__(self, other: TermLike) -> BinaryOp:
        return BinaryOp(OperatorTag.POW, self, to_term(other))

    def __rpow__(self, other: TermLike) -> BinaryOp:
        return BinaryOp(OperatorTag.POW, to_term(other), self)

    def __neg__(self) -> UnaryOp:
        return UnaryOp(OperatorTag.NEG, self)

    def to_formula(self, representer: Representer) -> str:
        return representer.represent_root(self)


@dataclass(frozen=True, slots=True)
class Constant(TermBase):
    expr: str


@dataclass(frozen=True, slots=True)
class ArrayConstant(TermBase):
    matrix: MatrixValue


@dataclass(frozen=True, slots=True)
class Ref(TermBase):
    key: int
    shape: Shape


@dataclass(frozen=True, slots=True)
class Materialized(TermBase):
    term: TermBase
    shape: Shape


@dataclass(frozen=True, slots=True)
class BinaryOp(TermBase):
    tag: OperatorTag
    left: TermBase
    right: TermBase


@dataclass(frozen=True, slots=True)
class UnaryOp(TermBase):
    tag: OperatorTag
    term: TermBase


def is_term_like(value: object) -> TypeGuard[TermLike]:
    if isinstance(value, TermBase):
        return True
    if _is_scalar(value):
        return True
    if _is_sequence(value):
        return True
    return False


def to_term(value: TermLike) -> TermBase:
    if isinstance(value, TermBase):
        return value
    if _is_scalar(value):
        return Constant(str(value))
    matrix = normalize_excel_value(value)
    return ArrayConstant(matrix)


def term_shape(term: TermBase) -> Shape:
    if isinstance(term, Constant):
        return (1, 1)
    if isinstance(term, ArrayConstant):
        return shape_of_matrix(term.matrix)
    if isinstance(term, Ref):
        return term.shape
    if isinstance(term, Materialized):
        return term.shape
    if isinstance(term, UnaryOp):
        if term.tag in {OperatorTag.SUM, OperatorTag.PRODUCT}:
            return (1, 1)
        return term_shape(term.term)
    if isinstance(term, BinaryOp):
        return broadcast_shape(term_shape(term.left), term_shape(term.right))
    raise TypeError(f'Unsupported term type: {type(term)}')


def abs(term: TermLike) -> UnaryOp:
    return UnaryOp(OperatorTag.ABS, to_term(term))


def round(term: TermLike, ndigits: TermLike) -> BinaryOp:
    return BinaryOp(OperatorTag.ROUND, to_term(term), to_term(ndigits))


def sqrt(term: TermLike) -> UnaryOp:
    return UnaryOp(OperatorTag.SQRT, to_term(term))


def log10(term: TermLike) -> UnaryOp:
    return UnaryOp(OperatorTag.LOG10, to_term(term))


def log(term: TermLike) -> UnaryOp:
    return UnaryOp(OperatorTag.LOG, to_term(term))


def sum(term: TermLike) -> UnaryOp:
    return UnaryOp(OperatorTag.SUM, to_term(term))


def product(term: TermLike) -> UnaryOp:
    return UnaryOp(OperatorTag.PRODUCT, to_term(term))


__all__ = [
    'ArrayConstant',
    'BinaryOp',
    'Constant',
    'ExcelArray1D',
    'ExcelArray2D',
    'ExcelScalar',
    'ExcelValue',
    'MatrixValue',
    'Materialized',
    'Notation',
    'OperatorTag',
    'Ref',
    'Shape',
    'TermBase',
    'TermLike',
    'UnaryOp',
    'abs',
    'broadcast_shape',
    'is_term_like',
    'log',
    'log10',
    'normalize_excel_value',
    'product',
    'round',
    'shape_of_matrix',
    'sqrt',
    'sum',
    'term_shape',
    'to_term',
]
