import cv2
import numpy as np
import pytest
from app.utils.barcode import decode_barcodes_from_image

def load_image(path: str) -> np.ndarray:
    img = cv2.imread(path)
    assert img is not None, f"Cannot load image {path}"
    return img

def test_decode_qr(tmp_path):
    img = load_image("tests/data/qr_code.png")
    results = decode_barcodes_from_image(img)
    assert isinstance(results, list)
    assert len(results) >= 1
    first = results[0]
    assert "text" in first and isinstance(first["text"], str) and first["text"]
    assert "format" in first and "QR" in first["format"]

def test_no_barcode(tmp_path):
    import numpy as np
    blank = np.zeros((200,200,3), dtype=np.uint8)
    results = decode_barcodes_from_image(blank)
    assert results == []
