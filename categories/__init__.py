"""Category handler registry for LocalMate."""

from categories import admin, medical

CATEGORY_HANDLERS = [admin, medical]

__all__ = ["CATEGORY_HANDLERS", "admin", "medical"]
