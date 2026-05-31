from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import xlwings as xw

from .term import (
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

if TYPE_CHECKING:
    from .evaluator import Allocator, Evaluator, ExcelResult


@dataclass(frozen=True, slots=True)
class CompiledTerm:
    root: TermBase
    refs: tuple[Ref, ...]
    output_shape: Shape


class Engine:
    def __init__(
        self,
        app: xw.App | None = None,
        start_row: int = 1,
        start_col: int = 1,
        max_width: int = 256,
        gap: int = 1,
    ) -> None:
        self._next_ref_key = 1
        self._bound_values: dict[Ref, MatrixValue] = {}
        self._evaluator: Evaluator | None = None

        if app is not None:
            self.configure_evaluator(
                app,
                start_row=start_row,
                start_col=start_col,
                max_width=max_width,
                gap=gap,
            )

    def configure_evaluator(
        self,
        app: xw.App,
        start_row: int = 1,
        start_col: int = 1,
        max_width: int = 256,
        gap: int = 1,
    ) -> None:
        from .evaluator import ArenaAllocator, Evaluator

        allocator = ArenaAllocator(
            start_row=start_row,
            start_col=start_col,
            max_width=max_width,
            gap=gap,
        )

        self._evaluator = Evaluator(
            app,
            allocator=allocator,
        )

    def configure_allocator(
        self,
        app: xw.App,
        start_row: int = 1,
        start_col: int = 1,
        max_width: int = 256,
        gap: int = 1,
    ) -> None:
        self.configure_evaluator(
            app,
            start_row=start_row,
            start_col=start_col,
            max_width=max_width,
            gap=gap,
        )

    def attach_evaluator(self, evaluator: Evaluator) -> None:
        self._evaluator = evaluator

    def attach_allocator(self, allocator: Allocator) -> None:
        if self._evaluator is None:
            raise RuntimeError(
                'Evaluator is not configured. Configure an evaluator before '
                'replacing its allocator.'
            )
        if not hasattr(self._evaluator, 'set_allocator'):
            raise TypeError('Current evaluator does not support allocator replacement.')
        self._evaluator.set_allocator(allocator)

    def create_ref(self, value: ExcelValue) -> Ref:
        matrix = normalize_excel_value(value)
        shape = (len(matrix), len(matrix[0]))
        ref = Ref(key=self._next_ref_key, shape=shape)
        self._next_ref_key += 1
        self._bound_values[ref] = matrix
        return ref

    def compile(self, term: TermLike) -> CompiledTerm:
        root = to_term(term)
        refs = self._collect_refs(root)
        for ref in refs:
            if ref not in self._bound_values:
                raise ValueError(
                    f'Reference key={ref.key} was not created by this engine instance.'
                )

        out_shape = term_shape(root)
        return CompiledTerm(root=root, refs=tuple(refs), output_shape=out_shape)

    def evaluate(self, term: TermLike) -> ExcelResult:
        if self._evaluator is None:
            raise RuntimeError(
                'Evaluator is not configured. Initialize Engine with app=... '
                'or call configure_evaluator(...).'
            )
        compiled = self.compile(term)
        return self._evaluator.execute(self, compiled)

    def bound_value(self, ref: Ref) -> MatrixValue:
        try:
            return self._bound_values[ref]
        except KeyError as exc:
            raise ValueError(
                f'Reference key={ref.key} was not created by this engine instance.'
            ) from exc

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


__all__ = ['CompiledTerm', 'Engine']
