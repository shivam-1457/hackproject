from app.routers.auth import router as auth_router
from app.routers.products import router as products_router
from app.routers.orders import router as orders_router
from app.routers.complaints import router as complaints_router
from app.routers.ratings import router as ratings_router
from app.routers.admin import router as admin_router

__all__ = [
    "auth_router",
    "products_router",
    "orders_router",
    "complaints_router",
    "ratings_router",
    "admin_router"
]
