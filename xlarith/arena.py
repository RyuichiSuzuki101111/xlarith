from .allocator import Allocator, ArenaAllocator, Rect

# Backward-compatible alias
Arena = ArenaAllocator

__all__ = ['Allocator', 'Arena', 'ArenaAllocator', 'Rect']
