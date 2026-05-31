from __future__ import annotations

from collections.abc import Sequence
from typing import TypeAlias

import xlwings as xw

from .arena import Arena, Rect
from .representer import ExcelRepresenter
from .term import (
    ExcelScalar,
    ExcelValue,
    MatrixValue,
    Ref,
    Shape,
    TermBase,
    TermLike,
    normalize_excel_value,
    term_shape,
    to_term,
)

ExcelResultScalar: TypeAlias = ExcelScalar | None
ExcelResult: TypeAlias = (
    ExcelResultScalar | list[ExcelResultScalar] | list[list[ExcelResultScalar]]
)


class Engine:
    def __init__(
        self,
        sheet: xw.Sheet,
        start_row: int = 1,
        start_col: int = 1,
        max_width: int = 100,
        gap: int = 1,
    ) -> None:
        self.sheet = sheet
        self._start_row = start_row
        self._start_col = start_col
        self._max_width = max_width
        self._gap = gap

        self._next_ref_key = 1
        self._bound_values: dict[Ref, MatrixValue] = {}

    def create_ref(self, value: ExcelValue) -> Ref:
        matrix = normalize_excel_value(value)
        shape = (len(matrix), len(matrix[0]))
        ref = Ref(key=self._next_ref_key, shape=shape)
        self._next_ref_key += 1
        self._bound_values[ref] = matrix
        return ref

    def evaluate(self, term: TermLike) -> ExcelResult:
        root = to_term(term)
        arena = Arena(
            start_row=self._start_row,
            start_col=self._start_col,
            max_width=self._max_width,
            gap=self._gap,
        )

        refs = self._collect_refs(root)
        addresses: dict[Ref, str] = {}
        for ref in refs:
            if ref not in self._bound_values:
                raise ValueError(
                    f'Reference key={ref.key} was not created by this engine instance.'
                )

            rect = arena.alloc(ref.shape[0], ref.shape[1])
            self._write_matrix(rect, self._bound_values[ref])
            addresses[ref] = self._rect_address(rect)

        out_shape = term_shape(root)
        out_rect = arena.alloc(out_shape[0], out_shape[1])
        out_range = self._rect_range(out_rect)
        out_range.clear_contents()

        representer = ExcelRepresenter(addresses)
        formula = '=' + representer.represent_root(root)
        self.sheet.cells(out_rect.row, out_rect.col).formula = formula
        self.sheet.book.app.calculate()

        raw = out_range.value
        return self._normalize_result(raw, out_shape)

    def _collect_refs(self, term: TermBase) -> list[Ref]:
        ordered_refs: list[Ref] = []
        seen: set[Ref] = set()

        def visit(node: TermBase) -> None:
            from .term import BinaryOp, UnaryOp

            if isinstance(node, Ref):
                if node not in seen:
                    seen.add(node)
                    ordered_refs.append(node)
                return

            if isinstance(node, UnaryOp):
                visit(node.term)
                return

            if isinstance(node, BinaryOp):
                visit(node.left)
                visit(node.right)
                return

        visit(term)
        return ordered_refs

    def _write_matrix(self, rect: Rect, matrix: MatrixValue) -> None:
        target = self._rect_range(rect)
        if rect.height == 1 and rect.width == 1:
            target.value = matrix[0][0]
            return

        target.value = [list(row) for row in matrix]

    def _rect_range(self, rect: Rect) -> xw.Range:
        return self.sheet.range(
            (rect.row, rect.col),
            (rect.row + rect.height - 1, rect.col + rect.width - 1),
        )

    def _rect_address(self, rect: Rect) -> str:
        return self._rect_range(rect).get_address(
            row_absolute=False,
            column_absolute=False,
            include_sheetname=False,
            external=False,
        )

    def _normalize_result(self, raw: object, shape: Shape) -> ExcelResult:
        rows, cols = shape
        if rows == 1 and cols == 1:
            if isinstance(raw, list):
                if raw and isinstance(raw[0], list):
                    return raw[0][0]
                if raw:
                    return raw[0]
            return raw if raw is None or isinstance(raw, (int, float, str)) else None

        matrix = self._coerce_matrix(raw, shape)
        if rows == 1:
            return matrix[0]
        if cols == 1:
            return [row[0] for row in matrix]
        return matrix

    def _coerce_matrix(
        self,
        raw: object,
        shape: Shape,
    ) -> list[list[ExcelResultScalar]]:
        rows, cols = shape

        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
            if rows == 1 and cols > 1:
                if raw and isinstance(raw[0], list):
                    return [list(raw[0])]
                return [list(raw)]

            if rows > 1 and cols == 1:
                if raw and isinstance(raw[0], list):
                    return [list(item) for item in raw]
                return [[item] for item in raw]

            if raw and isinstance(raw[0], list):
                return [list(item) for item in raw]

        # xlwings can return a scalar in edge cases even for ranges.
        scalar = raw if raw is None or isinstance(raw, (int, float, str)) else None
        return [[scalar for _ in range(cols)] for _ in range(rows)]


__all__ = ['Engine', 'ExcelResult', 'ExcelResultScalar']
