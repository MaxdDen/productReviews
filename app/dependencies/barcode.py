from fastapi import Depends, UploadFile, HTTPException, status
import numpy as np
import cv2
from . import get_current_user  # пример зависимости
from app.utils.barcode import decode_barcodes_from_image

async def get_barcodes_from_upload(
    file: UploadFile,
    user = Depends(get_current_user),
) -> list[dict]:
    contents = await file.read()
    arr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image")
    return decode_barcodes_from_image(img)
