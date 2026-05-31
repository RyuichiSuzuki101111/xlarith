"""Compatibility shim for placement symbols."""

# isort: skip_file

from .placement import Allocator, ArenaAllocator, Rect, EXCEL_MAX_COLUMNS

__all__ = ('EXCEL_MAX_COLUMNS', 'Allocator', 'ArenaAllocator', 'Rect')
