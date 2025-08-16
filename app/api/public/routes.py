from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.templates import templates


router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

@router.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse(request, "about.html", {"request": request})

@router.get("/contacts", response_class=HTMLResponse)
def contacts(request: Request):
    return templates.TemplateResponse(request, "contacts.html", {"request": request})

@router.get("/policy", response_class=HTMLResponse)
def policy(request: Request):
    return templates.TemplateResponse(request, "policy.html", {"request": request})
