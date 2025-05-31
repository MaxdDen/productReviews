from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/debug/csrf-test")
async def csrf_test_post(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    return {"message": "POST прошёл успешно", "data": data}


@router.get("/test")
async def test(request: Request):
    print(f"test_...: {uuid.uuid4()}, path: {request.url.path}, query: {dict(request.query_params)}")
    return {"ok": True}