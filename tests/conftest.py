from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.session import get_db



# --- Роут: получить пользователя по username ---
def create_test_app():
    app = FastAPI()
    @app.get("/users/{username}")
    async def get_user(username: str, db: Session = Depends(get_db)):
        ...
    return app

# --- Тесты ---
def create_test_session():
    app = FastAPI()
    @app.get("/test-session")
    async def test_session(request: Request):
        visits = request.session.get("visits", 0) + 1
        request.session["visits"] = visits

        return JSONResponse({
            "session": dict(request.session),
            "message": "Сессия работает",
            "visits": visits
        })