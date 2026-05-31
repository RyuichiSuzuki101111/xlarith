from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, TypeAlias

from .representer import ExcelRepresenter
from .term import ExcelScalar, Materialized, MatrixValue, Ref, Shape

if TYPE_CHECKING:
    import xlwings as xw

    from .compiler import CompiledTerm
    from .engine import Engine
    from .placement import Allocator, Rect


ExcelResultScalar: TypeAlias = ExcelScalar | None
ExcelResult: TypeAlias = (
    ExcelResultScalar | list[ExcelResultScalar] | list[list[ExcelResultScalar]]
)


class Evaluator:
    def __init__(
        self,
        app: xw.App | None,
        allocator: Allocator,
    ) -> None:
        self.app = app
        self._allocator = allocator

    def set_allocator(self, allocator: Allocator) -> None:
        self._allocator = allocator

    def evaluate(self, engine: Engine, term: object) -> ExcelResult:
        compiled = engine.compile(term)
        return self.execute(engine, compiled)

    def execute(self, engine: Engine, compiled: CompiledTerm) -> ExcelResult:
        if self.app is None:
            msg = 'Excel app is not configured for evaluation.'
            raise RuntimeError(msg)

        addresses: dict[Ref | Materialized, str] = {}
        for ref in compiled.refs:
            matrix = engine.bound_value(ref)
            rect = self._allocator.alloc(ref.shape[0], ref.shape[1])
            self._write_matrix(rect, matrix)
            addresses[ref] = self._rect_address(rect)

        representer = ExcelRepresenter(addresses)
        for materialized in compiled.materialized:
            mat_shape = materialized.shape
            mat_rect = self._allocator.alloc(mat_shape[0], mat_shape[1])
            mat_range = self._rect_range(mat_rect)
            mat_range.clear_contents()

            formula = '=' + representer.represent(materialized.term)
            if mat_shape == (1, 1):
                self.app.range((mat_rect.row, mat_rect.col)).formula = formula
            else:
                mat_range.formula_array = formula
            addresses[materialized] = self._rect_address(mat_rect)

        out_shape = compiled.output_shape
        out_rect = self._allocator.alloc(out_shape[0], out_shape[1])
        out_range = self._rect_range(out_rect)
        out_range.clear_contents()

        representer = ExcelRepresenter(addresses)
        formula = '=' + representer.represent_root(compiled.root)
        print(f'Writing formula to Excel: {formula}')
        if out_shape == (1, 1):
            self.app.range((out_rect.row, out_rect.col)).formula = formula
        else:
            # Use array formulas for fixed-shape vector/matrix outputs.
            out_range.formula_array = formula
        self.app.calculate()

        raw = out_range.value
        print(f'Raw result from Excel: {raw}')
        return self._normalize_result(raw, out_shape)

    def _write_matrix(self, rect: Rect, matrix: MatrixValue) -> None:
        target = self._rect_range(rect)
        if rect.height == 1 and rect.width == 1:
            target.value = matrix[0][0]
            return

        target.value = [list(row) for row in matrix]

    def _rect_range(self, rect: Rect) -> xw.Range:
        return self.app.range(
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
            return raw if raw is None or isinstance(raw, int | float | str) else None

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

        if isinstance(raw, Sequence) and not isinstance(raw, str | bytes | bytearray):
            return self._coerce_matrix_from_sequence(raw, shape)

        # xlwings can return a scalar in edge cases even for ranges.
        scalar = raw if raw is None or isinstance(raw, int | float | str) else None
        return [[scalar for _ in range(cols)] for _ in range(rows)]

    def _coerce_matrix_from_sequence(
        self,
        raw: Sequence[object],
        shape: Shape,
    ) -> list[list[ExcelResultScalar]]:
        rows, cols = shape
        matrix: list[list[ExcelResultScalar]] = [
            [None for _ in range(cols)] for _ in range(rows)
        ]

        outer = list(raw)
        if not outer:
            return matrix

        first = outer[0]
        is_nested = isinstance(first, Sequence) and not isinstance(
            first,
            str | bytes | bytearray,
        )

        if is_nested:
            for r in range(min(rows, len(outer))):
                row_obj = outer[r]
                if not isinstance(row_obj, Sequence) or isinstance(
                    row_obj,
                    str | bytes | bytearray,
                ):
                    if cols > 0:
                        matrix[r][0] = self._to_excel_result_scalar(row_obj)
                    continue

                row_values = list(row_obj)
                for c in range(min(cols, len(row_values))):
                    matrix[r][c] = self._to_excel_result_scalar(row_values[c])
            return matrix

        if rows == 1:
            for c in range(min(cols, len(outer))):
                matrix[0][c] = self._to_excel_result_scalar(outer[c])
            return matrix

        if cols == 1:
            for r in range(min(rows, len(outer))):
                matrix[r][0] = self._to_excel_result_scalar(outer[r])
            return matrix

        # Fallback: map flat sequences into a matrix in row-major order.
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= len(outer):
                    return matrix
                matrix[r][c] = self._to_excel_result_scalar(outer[idx])
                idx += 1
        return matrix

    def _to_excel_result_scalar(self, value: object) -> ExcelResultScalar:
        return value if value is None or isinstance(value, int | float | str) else None


__all__ = ['Evaluator', 'ExcelResult', 'ExcelResultScalar']
