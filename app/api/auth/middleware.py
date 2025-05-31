from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, timezone

from app.templates import templates
from app.core import settings
from app.database import SessionLocal
from app.models import User


PUBLIC_PATHS = [
    "/", "/about", "/contacts", "/policy", "/auth",
    "/favicon.ico", "/static", "/403", "/404", "/500",
    "/docs", "/openapi.json", "/redoc", "/docs/oauth2-redirect"
]

PRIVATE_PATHS = [
    "/dashboard", "/analyze", "/analyze_product", "/profile", "/product", "/upload",
    "/logout", "/directory", "/record", "/parse-reviews-file"
]

SERVICE_PREFIXES = [
    "/.well-known", "/static", "/docs", "/openapi.json", "/redoc"
]


class AuthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def receive_wrapper():
            return await receive()

        request = Request(scope, receive=receive)
        path = request.url.path

        if any(path.startswith(prefix) for prefix in SERVICE_PREFIXES):
            await self.app(scope, receive, send)
            return
        
        # Разрешить публичные пути
        if any(path == pub or path.startswith(pub + "/") for pub in PUBLIC_PATHS):
            await self.app(scope, receive, send)
            return

        # Защитить приватные пути
        if any(path == priv or path.startswith(priv + "/") for priv in PRIVATE_PATHS):
            token = request.cookies.get("access_token")

            if not token:
                if request.method == "GET":
                    response = RedirectResponse(url=f"/login?next={path}", status_code=302)
                else:
                    response = JSONResponse(status_code=401, content={"detail": "Not authenticated"})
                await response(scope, receive, send)
                return

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                user_id = int(payload.get("sub"))
                if not user_id:
                    raise JWTError("Missing subject")
                user_id = int(user_id) 

                db: Session = SessionLocal()
                user = db.query(User).filter(User.id == user_id).first()
                db.close()

                if not user:
                    raise JWTError("User not found")

                scope["state"]["user"] = user
                await self.app(scope, receive, send)
                return

            except JWTError as e:
                if request.method == "GET":
                    response = RedirectResponse(url="/login", status_code=302)
                else:
                    response = JSONResponse(status_code=401, content={"detail": "Invalid token"})
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
