"""Compilation helpers for turning terms into executable evaluation plans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .term import (
    BinaryOp,
    Materialized,
    Ref,
    Shape,
    TermBase,
    TermLike,
    UnaryOp,
    term_shape,
    to_term,
)

if TYPE_CHECKING:
    from .engine import Engine


@dataclass(frozen=True, slots=True)
class CompiledTerm:
    """Compiled execution plan produced from a root term."""

    root: TermBase
    refs: tuple[Ref, ...]
    materialized: tuple[Materialized, ...]
    output_shape: Shape


class Compiler:
    """Collect refs and materialized nodes required for evaluator execution."""

    def compile(self, engine: Engine, term: TermLike) -> CompiledTerm:
        """Compile a term and validate that all references belong to the engine."""
        root = to_term(term)
        refs = self.collect_refs(root)
        materialized = self.collect_materialized(root)
        for ref in refs:
            if ref not in engine._bound_values:
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

    def collect_refs(self, term: TermBase) -> list[Ref]:
        """Collect unique Ref nodes in traversal order."""
        ordered_refs: list[Ref] = []
        seen: set[Ref] = set()

        def visit(node: TermBase) -> None:
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

    def collect_materialized(self, term: TermBase) -> list[Materialized]:
        """Collect unique Materialized nodes in dependency-safe order."""
        ordered_terms: list[Materialized] = []
        seen: set[Materialized] = set()

        def visit(node: TermBase) -> None:
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


__all__ = ('CompiledTerm', 'Compiler')
