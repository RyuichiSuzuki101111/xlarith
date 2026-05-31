"""User-facing API for building and evaluating Excel-backed expressions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

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

if TYPE_CHECKING:
    import xlwings as xw


class Engine:
    """Main interface for creating refs, compiling terms, and evaluating formulas.

    Quick example:

    ```python
    import xlwings as xw
    import xlarith as xa

    app = xw.App(visible=False, add_book=True)
    try:
        eng = xa.Engine(app)
        a = eng.create_ref([1, 2, 3])
        result = eng.evaluate(xa.wf.round(a + 0.5, 0))
        # result -> [2, 3, 4]
    finally:
        app.quit()
    ```

    """

    def __init__(
        self,
        app: xw.App | None = None,
        allocator: Allocator | None = None,
    ) -> None:
        """Initialize the engine with an optional Excel app and allocator."""
        self._next_ref_key = 1
        self._bound_values: dict[Ref, MatrixValue] = {}
        self._allocator = allocator or ArenaAllocator()
        self._compiler = Compiler()
        self._evaluator = Evaluator(app, self._allocator)

    def create_ref(
        self,
        value: ExcelValue,
        *,
        vector_orientation: Literal['row', 'column'] = 'row',
    ) -> Ref:
        """Register a Python value and return a symbolic ref.

        For 1D sequence inputs, ``vector_orientation`` controls whether the
        sequence is interpreted as a row vector ``(1, n)`` or a column vector
        ``(n, 1)``.
        """
        if vector_orientation not in {'row', 'column'}:
            msg = (
                "vector_orientation must be either 'row' or 'column'. "
                f'Got: {vector_orientation!r}'
            )
            raise ValueError(msg)

        matrix = normalize_excel_value(value)
        if self._is_1d_sequence(value) and vector_orientation == 'column':
            matrix = tuple((item,) for item in matrix[0])

        shape = (len(matrix), len(matrix[0]))
        ref = Ref(key=self._next_ref_key, shape=shape)
        self._next_ref_key += 1
        self._bound_values[ref] = matrix
        return ref

    def _is_1d_sequence(self, value: ExcelValue) -> bool:
        if not isinstance(value, Sequence) or isinstance(
            value,
            str | bytes | bytearray,
        ):
            return False
        if len(value) == 0:
            return False
        first = value[0]
        return not (
            isinstance(first, Sequence)
            and not isinstance(first, str | bytes | bytearray)
        )

    def materialize(self, term: TermLike) -> Materialized:
        """Mark a sub-expression to be placed in a temporary Excel range."""
        base = to_term(term)
        return Materialized(term=base, shape=term_shape(base))

    def compile(self, term: TermLike) -> CompiledTerm:
        """Compile a term into an execution plan with refs and output shape."""
        return self._compiler.compile(self, term)

    def evaluate(self, term: TermLike) -> ExcelResult:
        """Compile and execute a term in Excel, then normalize the returned value."""
        if self._evaluator is None:
            msg = (
                'Evaluator is not configured. Initialize Engine with app=... '
                'or call configure_evaluator(...).'
            )
            raise RuntimeError(msg)
        compiled = self.compile(term)
        return self._evaluator.execute(self, compiled)

    def bound_value(self, ref: Ref) -> MatrixValue:
        """Get the matrix value associated with a ref created by this engine."""
        try:
            return self._bound_values[ref]
        except KeyError as exc:
            msg = f'Reference key={ref.key} was not created by this engine instance.'
            raise ValueError(msg) from exc

    def _collect_refs(self, term: TermBase) -> list[Ref]:
        return self._compiler.collect_refs(term)

    def _collect_materialized(self, term: TermBase) -> list[Materialized]:
        return self._compiler.collect_materialized(term)


__all__ = ('CompiledTerm', 'Engine')
