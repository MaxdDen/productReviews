from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from typing import Optional # For type hinting
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession # Still needed for type hinting
from urllib.parse import quote

from app.core.config import settings
# from app.database.session import AsyncSessionLocal # No longer directly used by AuthMiddleware
from app.models import User

PUBLIC_PATHS = [
    "/", "/about", "/contacts", "/policy",
    "/login", "/register",  # Ensure these are explicitly public
    # "/auth", # This might be redundant if /login and /register are specific
    "/favicon.ico", "/static", "/403", "/404", "/500",
    "/docs", "/openapi.json", "/redoc", "/docs/oauth2-redirect"
]

# PRIVATE_PATHS is not directly used by the logic below for access control,
# but rather PUBLIC_PATHS and SERVICE_PREFIXES are used to bypass auth.
# PRIVATE_PATHS = [
#     "/dashboard", "/analyze", "/analyze_product", "/profile", "/product", "/upload",
#     "/logout", "/directory", "/record", "/parse-reviews-file"
# ]

SERVICE_PREFIXES = [
    "/.well-known", "/static", "/docs", "/openapi.json", "/redoc"
]

# Ensure that any path not in PUBLIC_PATHS or SERVICE_PREFIXES is considered private
# and requires authentication.

class AuthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        path = request.url.path

        if any(path.startswith(prefix) for prefix in SERVICE_PREFIXES + PUBLIC_PATHS):
            await self.app(scope, receive, send)
            return

        token = request.cookies.get("access_token")
        if not token:
            await self._reject(request, send, reason="Not authenticated")
            return

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = int(payload.get("sub"))

            db_session: Optional[AsyncSession] = scope.get("state", {}).get("db")

            if db_session is None:
                # This indicates a server configuration error, as DatabaseMiddleware should have set this.
                # Or, for tests, a test-specific middleware should have set it.
                # logger.error("AuthMiddleware: Database session not found in request scope.")
                await self._reject(request, send, reason="Server configuration error - DB session missing")
                return

            user = await db_session.get(User, user_id)

            if not user:
                raise JWTError("User not found") # This will be caught by the except JWTError block

            scope["state"]["user"] = user
            await self.app(scope, receive, send)
        except JWTError:
            # This will catch JWTError from decode, or if user not found.
            # No specific db rollback needed here for read operations or if commit is handled by get_db.
            await self._reject(request, send, reason="Invalid token or user not found")

    async def _reject(self, request: Request, send: Send, reason: str):
        if request.method == "GET":
            # Store the original URL (path + query) in a 'next' query parameter, properly URL-encoded
            original_path_and_query = request.url.path
            if request.url.query:
                original_path_and_query += f"?{request.url.query}"

            encoded_next_url = quote(original_path_and_query, safe="/?=&")
            redirect_url = f"/login?next={encoded_next_url}"
            response = RedirectResponse(url=redirect_url, status_code=302)
        else:
            response = JSONResponse(status_code=401, content={"detail": reason})
        await response(request.scope, request.receive, send)
