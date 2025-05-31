from fastapi import FastAPI, Body
from pydantic import BaseModel

app = FastAPI()

class AnalyzeFilters(BaseModel):
    promt_id: str = ""

@app.post("/test")
async def test(filters: AnalyzeFilters = Body(..., embed=False)):
    return filters