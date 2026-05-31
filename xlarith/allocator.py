"""Compatibility shim for placement symbols."""

# isort: skip_file

from .placement import Allocator, ArenaAllocator, Rect, EXCEL_MAX_COLUMNS

__all__ = ['Allocator', 'ArenaAllocator', 'Rect', 'EXCEL_MAX_COLUMNS']
