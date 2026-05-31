from __future__ import annotations

import xlwings as xw

from .compiler import CompiledTerm, Compiler
from .evaluator import Evaluator, ExcelResult
from .placement import Allocator, ArenaAllocator
from .term import (
    ExcelValue,
    Materialized,
    MatrixValue,
    Ref,
    TermBase,
    TermLike,
    normalize_excel_value,
    term_shape,
    to_term,
)


class Engine:
    def __init__(
        self,
        app: xw.App | None = None,
        allocator: Allocator | None = None,
    ) -> None:
        self._next_ref_key = 1
        self._bound_values: dict[Ref, MatrixValue] = {}
        self._allocator = allocator or ArenaAllocator()
        self._compiler = Compiler()
        self._evaluator = Evaluator(app, self._allocator)

    def create_ref(self, value: ExcelValue) -> Ref:
        matrix = normalize_excel_value(value)
        shape = (len(matrix), len(matrix[0]))
        ref = Ref(key=self._next_ref_key, shape=shape)
        self._next_ref_key += 1
        self._bound_values[ref] = matrix
        return ref

    def materialize(self, term: TermLike) -> Materialized:
        base = to_term(term)
        return Materialized(term=base, shape=term_shape(base))

    def compile(self, term: TermLike) -> CompiledTerm:
        return self._compiler.compile(self, term)

    def evaluate(self, term: TermLike) -> ExcelResult:
        if self._evaluator is None:
            msg = (
                'Evaluator is not configured. Initialize Engine with app=... '
                'or call configure_evaluator(...).'
            )
            raise RuntimeError(msg)
        compiled = self.compile(term)
        return self._evaluator.execute(self, compiled)

    def bound_value(self, ref: Ref) -> MatrixValue:
        try:
            return self._bound_values[ref]
        except KeyError as exc:
            msg = f'Reference key={ref.key} was not created by this engine instance.'
            raise ValueError(msg) from exc

    def _collect_refs(self, term: TermBase) -> list[Ref]:
        return self._compiler.collect_refs(term)

    def _collect_materialized(self, term: TermBase) -> list[Materialized]:
        return self._compiler.collect_materialized(term)


__all__ = ['CompiledTerm', 'Engine']
