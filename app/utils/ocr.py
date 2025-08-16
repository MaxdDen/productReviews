import os
import shutil
import pytesseract
from typing import Optional

_initialized = False

def _init_tesseract():
    global _initialized
    if _initialized:
        return

    cmd = os.getenv("TESSERACT_CMD")
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd.strip('"')
    elif not shutil.which("tesseract"):
        raise RuntimeError(
            "Tesseract не найден: установите tesseract и добавьте в PATH, "
            "или задайте TESSERACT_CMD в окружении."
        )
    # Если всё ок — помечаем, чтобы не инициализировать повторно
    _initialized = True

def ocr_image_to_text(image) -> str:
    """
    Применяет OCR к изображению (PIL или NumPy), возвращает распознанный текст.
    """
    _init_tesseract()
    return pytesseract.image_to_string(image)

def ocr_image_to_data(image) -> dict:
    """
    Возвращает детализированную структуру (dataframe-like dict) из pytesseract.
    """
    _init_tesseract()
    return pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
