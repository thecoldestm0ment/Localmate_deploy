"""Category handler registry for LocalMate."""

from dataclasses import dataclass

from categories import admin, medical, traffic


@dataclass(frozen=True)
class CategoryHandlerSpec:
    module: object
    priority: int


CATEGORY_REGISTRY = (
    CategoryHandlerSpec(admin, getattr(admin, "ROUTE_PRIORITY", 0)),
    CategoryHandlerSpec(medical, getattr(medical, "ROUTE_PRIORITY", 0)),
    CategoryHandlerSpec(traffic, getattr(traffic, "ROUTE_PRIORITY", 0)),
)

CATEGORY_HANDLERS = [spec.module for spec in CATEGORY_REGISTRY]

__all__ = [
    "CATEGORY_HANDLERS",
    "CATEGORY_REGISTRY",
    "CategoryHandlerSpec",
    "admin",
    "medical",
    "traffic",
]
