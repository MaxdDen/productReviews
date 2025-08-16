from fastapi import APIRouter, UploadFile, File, Form, Depends, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List

from app.templates import templates
from app.utils.query_params import extract_dashboard_filters
from app.utils.security import template_with_csrf
from app.database import get_db
from app.services.identify_service import identify_from_images
from app.schemas.product import ProductIdentifyResponse


router = APIRouter()


@router.get("/identify", response_class=HTMLResponse)
async def identify_page(request: Request):
    filters = extract_dashboard_filters(request)
    context = {
        "request": request,
        **filters
    }    
    return template_with_csrf(request, templates, "identify.html", context)


@router.post("/identify", response_model=ProductIdentifyResponse)
async def identify_product(
    request: Request,
    images: List[UploadFile] = File(...),
    save_to_product: bool = Form(True),
    db: Session = Depends(get_db),
):
    try:
        result = await identify_from_images(images, db, save_to_product)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
