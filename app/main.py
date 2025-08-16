"""
AI Review Analyzer - FastAPI Application Entry Point

Manages product listings, reviews analysis, and directory management
for international company automation.
"""

import logging
from app.core import setup_logging

# Setup logging before any other imports
setup_logging()
logger = logging.getLogger(__name__)

import asyncio
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# Core configuration and database
from app.core.config import settings
from app.database.init_db import init_db

# Middleware
from app.core.middleware.auth_middleware import AuthMiddleware
from app.core.middleware.db_middleware import DatabaseMiddleware
from app.core.middleware.security_headers import SecurityHeadersMiddleware

# API Routers
from app.api import (
    analysis_router,
    auth_router,
    private_router,
    product_router,
    public_router,
)
from app.api.directory_router_factory import create_directory_router

# Models and Schemas
from app.models import Brand, Category, Promt
from app.schemas import (
    Brand as BrandSchema,
    BrandCreate,
    BrandUpdate,
    Category as CategorySchema,
    CategoryCreate,
    CategoryUpdate,
    Promt as PromtSchema,
    PromtCreate,
    PromtUpdate,
)


# --- Application lifespan management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources."""
    logger.info("Starting AI Review Analyzer application")
    
    try:
        # Initialize database in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, init_db)
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    yield
    
    logger.info("Shutting down AI Review Analyzer application") 

# --- FastAPI Application Configuration ---
app = FastAPI(
    title="AI Review Analyzer",
    description="International company automation: product listings, supplier management, and AI review analysis",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# --- Static files ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --- Middleware configuration ---
# Order matters: DatabaseMiddleware must run before any middleware requiring DB session
middleware_config = [
    (DatabaseMiddleware, {}),
    (SessionMiddleware, {
        "secret_key": settings.SECRET_KEY,
        "session_cookie": "session",
        "https_only": settings.is_production,
        "same_site": "strict" if settings.is_production else "lax"
    }),
    (AuthMiddleware, {}),
    (SecurityHeadersMiddleware, {})
]

for middleware_class, kwargs in middleware_config:
    app.add_middleware(middleware_class, **kwargs)

# --- Роутеры ---
app.include_router(auth_router)
app.include_router(public_router)
app.include_router(private_router)
app.include_router(product_router) # Assuming product routes are at /product or similar, not /api/product
app.include_router(analysis_router) # Assuming analysis routes are not /api/analysis

# --- Directory routers configuration ---
def setup_directory_routers() -> List[tuple]:
    """Configure directory routers using factory pattern."""
    directory_configs = [
        {
            "model": Brand,
            "schema": BrandSchema,
            "create_schema": BrandCreate,
            "update_schema": BrandUpdate,
            "prefix": "/api/brand",
            "tags": ["Brands"]
        },
        {
            "model": Category,
            "schema": CategorySchema,
            "create_schema": CategoryCreate,
            "update_schema": CategoryUpdate,
            "prefix": "/api/category",
            "tags": ["Categories"]
        },
        {
            "model": Promt,
            "schema": PromtSchema,
            "create_schema": PromtCreate,
            "update_schema": PromtUpdate,
            "prefix": "/api/promt",
            "tags": ["Promts"]
        }
    ]
    
    routers = []
    for config in directory_configs:
        router = create_directory_router(**config)
        routers.append(router)
        logger.info(f"Created directory router for {config['prefix']}")
    
    return routers

# Create and register directory routers
directory_routers = setup_directory_routers()
for router in directory_routers:
    app.include_router(router)


logger.info(f"Running in {'production' if settings.is_production else 'development'} mode")


# --- Global exception handlers ---
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 Not Found errors."""
    logger.warning(f"404 Not Found: {request.url}")
    return HTMLResponse(
        content="<h1>404 - Page Not Found</h1><p>The requested page could not be found.</p>",
        status_code=404
    )

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    """Handle 500 Internal Server Error."""
    logger.error(f"500 Internal Server Error: {request.url} - {exc}")
    return HTMLResponse(
        content="<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>",
        status_code=500
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True, log_level="warning")
    