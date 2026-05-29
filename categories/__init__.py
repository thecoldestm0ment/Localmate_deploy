"""Category handler registry for LocalMate."""

from categories import admin, medical, traffic

CATEGORY_HANDLERS = [
    admin,
    medical,
    traffic,
]

__all__ = ["CATEGORY_HANDLERS", "admin", "medical", "traffic"]
