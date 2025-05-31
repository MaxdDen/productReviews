from fastapi import FastAPI, Depends, Body, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class AnalyzeFilters(BaseModel):
    promt_id: Optional[str] = None

def csrf_protect(request: Request, csrf_token: str = None):
    pass  # Твой код неважен для структуры body

@app.post("/test")
async def test(
    filters: AnalyzeFilters = Body(..., embed=False),
    _: None = Depends(csrf_protect)
):
    return filters
