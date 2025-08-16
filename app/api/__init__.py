from app.api.auth.routes import router as auth_router
from app.api.product.routes import router as product_router
from app.api.analysis.routes import router as analysis_router
from app.api.public.routes import router as public_router
from app.api.private.routes import router as private_router

__all__ = [
    "auth_router",
    "product_router",
    "analysis_router",
    "public_router",
    "private_router",
]