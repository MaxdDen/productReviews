from passlib.context import CryptContext
from fastapi import Request, HTTPException, Form
from fastapi.requests import Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from jose import jwt
from secrets import token_urlsafe
from datetime import datetime, timedelta, timezone

from app.core import settings


# --- Пароль ---
# Используем argon2 как современный алгоритм хеширования 
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    """Хеширует пароль."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля и его хеша."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# --- JWT токены ---
def create_jwt_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# --- CSRF ---
def generate_csrf_token() -> str:
    return token_urlsafe(32)

def ensure_csrf_token(request: Request) -> str:
    csrf_token = request.cookies.get("csrf_token")
    if not csrf_token:
        csrf_token = generate_csrf_token()
    return csrf_token

def csrf_protect(request: Request):
    header_token = request.headers.get("X-CSRF-Token")
    cookie_token = request.cookies.get("csrf_token")

    if not cookie_token or not header_token or cookie_token != header_token:
        raise HTTPException(403, "Invalid CSRF token.")    

def template_with_csrf(
    request: Request,
    templates: Jinja2Templates,
    template_name: str,
    context: dict,
    *,
    httponly: bool = False,
    samesite: str = "Lax"
) -> Response:
    csrf_token = ensure_csrf_token(request)
    context["csrf_token"] = csrf_token
    response = templates.TemplateResponse(template_name, context)
    response.set_cookie(
        "csrf_token",
        csrf_token,
        httponly=httponly,
        samesite=samesite,
        path="/"
    )
    return response