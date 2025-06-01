from app.core import setup_logging
setup_logging()

import sys
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

# --- Локальные импорты ---
from app.templates import templates
from app.core.config import settings, is_production_env
from app.database.session import get_db
from app.database.crud import get_user_by_username
from app.utils.headers_middleware import SecurityHeadersMiddleware
from app.api import (
    analysis_router,
    auth_router,
    AuthMiddleware,
    private_router,
    product_router,
    public_router
)


# --- Lifespan context ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

# --- Инициализация FastAPI ---
app = FastAPI(lifespan=lifespan)

# --- Подключение статики ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --- Middleware ---
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="session",
    https_only=is_production_env(settings),
    same_site="strict" if is_production_env(settings) else "lax"
)
app.add_middleware(AuthMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# --- Роутеры ---
app.include_router(auth_router)
app.include_router(public_router)
app.include_router(private_router)
app.include_router(product_router)
app.include_router(analysis_router)


print(f"Running in {'production' if is_production_env(settings) else 'development'} mode")


# --- Обработка ошибок ---
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def internal_error(request: Request, exc):
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True, log_level="warning")
    