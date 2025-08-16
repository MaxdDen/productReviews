import cv2
import numpy as np
import zxingcpp


from typing import List, Dict

def decode_barcodes_from_image(image: np.ndarray) -> list[dict]:
    """
    Принимает NumPy‑массив BGR (OpenCV), возвращает список словарей:
    [{'text': ..., 'format': ..., 'position': ...}, ...]
    """
    results = zxingcpp.read_barcodes(image)
    decoded = []
    for r in results:
        decoded.append({
            "text": r.text,
            "format": r.format.name if hasattr(r.format, "name") else str(r.format),
            "position": {
                "top_left": (r.position.top_left.x, r.position.top_left.y),
                "top_right": (r.position.top_right.x, r.position.top_right.y),
                "bottom_left": (r.position.bottom_left.x, r.position.bottom_left.y),
                "bottom_right": (r.position.bottom_right.x, r.position.bottom_right.y),
            }
        })
    return decoded

def extract_barcodes(image: np.ndarray) -> List[Dict]:
    """
    Обёртка над zxingcpp.read_barcodes для извлечения штрих-/QR-кодов.
    Возвращает список словарей вида:
    [{'text': ..., 'format': ..., 'position': {...}}, ...]
    """
    results = zxingcpp.read_barcodes(image)
    decoded = []
    for r in results:
        decoded.append({
            "text": r.text,
            "format": getattr(r.format, "name", str(r.format)),
            "position": {
                "top_left": (r.position.top_left.x, r.position.top_left.y),
                "top_right": (r.position.top_right.x, r.position.top_right.y),
                "bottom_left": (r.position.bottom_left.x, r.position.bottom_left.y),
                "bottom_right": (r.position.bottom_right.x, r.position.bottom_right.y),
            }
        })
    return decoded
