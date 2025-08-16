from app.core import settings

from fastapi import (
    APIRouter, Request, Depends, Response, HTTPException # Removed Form, status - not used
)
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession # Added AsyncSession
from sqlalchemy.future import select # Added select
from passlib.context import CryptContext
# from jose import jwt, JWTError # Not directly used in this file
# from fastapi.templating import Jinja2Templates # templates object is used directly
# from datetime import datetime, timedelta, timezone # Not directly used
from pydantic import BaseModel
from typing import Optional

from app.templates import templates
from app.database.session import get_db # Provides AsyncSession
from app.models import User
from app.utils.security import (
    hash_password, verify_password, create_jwt_token,
    csrf_protect, template_with_csrf # ensure_csrf_token not used
)
# from app.core.logging_config import csrf_logger, auth_logger # Not used
# import secrets # Not used


router = APIRouter()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto") # This is fine


class LoginInput(BaseModel):
    username: str
    password: str


@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request): # This can remain synchronous as it does no I/O
    context = {
        "request": request,
        "mode": "register"
    }
    return template_with_csrf(request, templates, "auth.html", context)

@router.post("/register")
async def register(
    register_input: LoginInput,
    _: None = Depends(csrf_protect), # Assuming csrf_protect is async compatible
    db: AsyncSession = Depends(get_db)
):
    if not register_input.username or not register_input.password:
        # Consider Pydantic validation for this
        raise HTTPException(status_code=400, detail="Все поля обязательны для заполнения")

    # Check if user exists
    stmt = select(User).filter(User.username == register_input.username)
    result = await db.execute(stmt)
    user_exists = result.scalar_one_or_none()

    if user_exists:
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")

    new_user = User(
        username=register_input.username,
        hashed_password=hash_password(register_input.password) # hash_password should be CPU bound
    )
    db.add(new_user)
    # await db.commit() # Middleware or test fixture handles commit/rollback
    await db.flush() # Flush to get ID for refresh, if needed, or ensure data is sent before potential refresh
    await db.refresh(new_user)

    return JSONResponse({"next": "/login"}) # Consider returning 201 Created status


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, next: str = "/dashboard"): # This can remain synchronous
    context = {
        "request": request,
        "mode": "login",
        "next": next
    }
    return template_with_csrf(request, templates, "auth.html", context)

from urllib.parse import urlparse, urljoin
from fastapi import Form

# ... (other imports)

@router.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    next_url: Optional[str] = Form(None), # Changed from LoginInput to Form parameters
    _: None = Depends(csrf_protect),
    db: AsyncSession = Depends(get_db)
):
    # Validate input using Pydantic if preferred, or manually
    if not username or not password:
        raise HTTPException(status_code=400, detail="Имя пользователя и пароль обязательны.")

    stmt = select(User).filter(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверные данные")

    jwt_token = create_jwt_token({"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=settings.is_production,
        samesite="Strict" if settings.is_production else "Lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    redirect_to = "/dashboard" # Default redirect
    if next_url:
        # Security: Validate next_url to prevent open redirect.
        # Allow only relative paths starting with '/' to prevent open redirects.
        parsed_next_url = urlparse(next_url)
        if not parsed_next_url.netloc and \
           not parsed_next_url.scheme and \
           parsed_next_url.path.startswith("/") and \
           not ("//" in parsed_next_url.path or "\\\\" in parsed_next_url.path or ":" in parsed_next_url.path):
            redirect_to = parsed_next_url.path
            if parsed_next_url.query:
                redirect_to += "?" + parsed_next_url.query
            # else, log a warning or handle as suspicious if needed (e.g. if path tried to be //example.com)
        # else:
            # Optionally, log that a potentially unsafe next_url was provided and ignored.
            # print(f"Warning: Potentially unsafe next_url discarded: {next_url}")

    return {"next": redirect_to}


@router.get("/logout", name="logout")
async def logout(request: Request): # No DB interaction, no changes needed for async here
    response = RedirectResponse(url="/", status_code=302) # status_code=status.HTTP_302_FOUND is more explicit
    response.delete_cookie("access_token")
    return response
