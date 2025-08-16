from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from app.database.session import AsyncSessionLocal

class DatabaseMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Гарантируем, что scope["state"] есть
        if "state" not in scope:
            scope["state"] = {}

        # If a session is already provided (e.g., by test fixtures), use it.
        # Otherwise, create a new one for the request.
        if "db" in scope["state"]:
            # Assuming the session in scope["state"]["db"] is managed elsewhere (e.g., tests)
            # including its lifecycle (commit, rollback, close).
            # Or, if this middleware should still manage it, the logic would be different.
            # For now, if 'db' is present, we assume it's fully managed.
            await self.app(scope, receive, send)
            return

        # If no session in scope, create and manage one.
        async with AsyncSessionLocal() as session:
            scope["state"]["db"] = session
            try:
                await self.app(scope, receive, send)
                # If no exception, assume success and commit the session
                # This middleware is the outermost layer for DB session management for actual requests.
                if session.is_active: # Ensure session wasn't closed or handled already
                    await session.commit()
            except Exception as e:
                # If an exception occurred, rollback the session
                if session.is_active:
                    await session.rollback()
                raise e
            # 'async with' ensures session.close() is called.
