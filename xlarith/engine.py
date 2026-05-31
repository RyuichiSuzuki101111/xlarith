from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import xlwings as xw

from .allocator import ArenaAllocator
from .evaluator import Evaluator, ExcelResult
from .term import (
    ExcelValue,
    Materialized,
    MatrixValue,
    Ref,
    Shape,
    TermBase,
    TermLike,
    normalize_excel_value,
    term_shape,
    to_term,
)

if TYPE_CHECKING:
    from .allocator import Allocator


@dataclass(frozen=True, slots=True)
class CompiledTerm:
    root: TermBase
    refs: tuple[Ref, ...]
    materialized: tuple[Materialized, ...]
    output_shape: Shape


class Engine:
    def __init__(
        self,
        app: xw.App | None = None,
        allocator: Allocator | None = None,
    ) -> None:
        self._next_ref_key = 1
        self._bound_values: dict[Ref, MatrixValue] = {}
        self._allocator = allocator or ArenaAllocator()
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
        root = to_term(term)
        refs = self._collect_refs(root)
        materialized = self._collect_materialized(root)
        for ref in refs:
            if ref not in self._bound_values:
                msg = (
                    f'Reference key={ref.key} was not created by this engine instance.'
                )
                raise ValueError(msg)

        out_shape = term_shape(root)
        return CompiledTerm(
            root=root,
            refs=tuple(refs),
            materialized=tuple(materialized),
            output_shape=out_shape,
        )

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
        ordered_refs: list[Ref] = []
        seen: set[Ref] = set()

        def visit(node: TermBase) -> None:
            from .term import BinaryOp, UnaryOp

            if isinstance(node, Ref):
                if node not in seen:
                    seen.add(node)
                    ordered_refs.append(node)
                return

            if isinstance(node, Materialized):
                visit(node.term)
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

    def _collect_materialized(self, term: TermBase) -> list[Materialized]:
        ordered_terms: list[Materialized] = []
        seen: set[Materialized] = set()

        def visit(node: TermBase) -> None:
            from .term import BinaryOp, UnaryOp

            if isinstance(node, Materialized):
                visit(node.term)
                if node not in seen:
                    seen.add(node)
                    ordered_terms.append(node)
                return

            if isinstance(node, UnaryOp):
                visit(node.term)
                return

            if isinstance(node, BinaryOp):
                visit(node.left)
                visit(node.right)
                return

        visit(term)
        return ordered_terms


__all__ = ['CompiledTerm', 'Engine']
