from app.core import settings

from fastapi import (
    APIRouter, Request, Form, Depends, status, Response, HTTPException
)
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

from app.templates import templates
from app.database import get_db
from app.models import User
from app.utils.security import (
    hash_password, verify_password, create_jwt_token,
    ensure_csrf_token, csrf_protect, template_with_csrf
)
from app.core.config import settings, is_production_env
import secrets


router = APIRouter()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class LoginInput(BaseModel):
    username: str
    password: str


@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    context = {
        "request": request,
        "mode": "register"
    }
    return template_with_csrf(request, templates, "auth.html", context)

@router.post("/register")
async def register(
    register_input: LoginInput,
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    if not register_input.username or not register_input.password:
        return JSONResponse({"detail": "Все поля обязательны для заполнения"}, status_code=400)

    user_exists = db.query(User).filter((User.username == register_input.username)).first()
    if user_exists:
        return JSONResponse({"detail": "Пользователь с таким именем уже существует"}, status_code=400)

    new_user = User(
        username=register_input.username,
        hashed_password=hash_password(register_input.password)
    )
    db.add(new_user)
    db.commit()

    return JSONResponse({"next": "/login"})



@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, next: str = "/dashboard"):
    context = {
        "request": request,
        "mode": "login",
        "next": next
    }
    return template_with_csrf(request, templates, "auth.html", context)

@router.post("/login")
async def login(
    login_input: LoginInput,
    response: Response,
    _: None = Depends(csrf_protect),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == login_input.username).first()
    if not user or not verify_password(login_input.password, user.hashed_password):
        return JSONResponse(status_code=401, content={"detail": "Неверные данные"})
    jwt_token = create_jwt_token({"sub": str(user.id)})
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=is_production_env(settings),
        samesite="Strict" if is_production_env(settings) else "Lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    return {"next": "/dashboard"}



@router.get("/logout", name="logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response
