import httpx
from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core import settings
from app.database import get_db
from app.models import Promt



async def analyze_reviews(
    reviewsBlock: list[str],
    promt_id: int | None = None,
    db: AsyncSession = Depends(get_db)
) -> str:    
    if 1==1:
        return "OOOOOOOOOOOOOOOOOOOOOOOOO."

    if not settings.OPENAI_API_KEY:
        return "ИИ-ключ не указан. Используется заглушка."

    titlePromt = "Проанализируй отзывы"
    if promt_id:
        promt = db.query(Promt).filter(Promt.id == promt_id).first()
        if promt and promt.description:
            titlePromt = f"{promt.description.strip()}"

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    userReviews = "Отзывы пользователей:"
    promtRreviews = f"{titlePromt}\n{userReviews}\n{reviewsBlock}"

    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": [{"role": "user", "content": f"{promtRreviews}"}],
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{settings.OPENAI_API_BASE}/chat/completions", headers=headers, json=payload)

            if response.status_code != 200:
                error_text = await response.aread()  # читаем весь текст ошибки
                print(f"❌ Ошибка от OpenAI: {response.status_code} {error_text.decode()}")
                raise HTTPException(status_code=500, detail="Ошибка при обращении к ИИ-сервису.")

            data = response.json()
            return data["choices"][0]["message"]["content"]

    except httpx.HTTPStatusError as e:
        print(f"🚨 HTTP ошибка: {e.response.status_code} {await e.response.aread()}")
        raise HTTPException(status_code=500, detail="Ошибка HTTP при обращении к ИИ-сервису.")
    except Exception as e:
        print(f"⚡ Общая ошибка при работе с ИИ: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при работе ИИ. Попробуйте позже.")



def fake_analysis(reviews: list[str]) -> str:
    """Функция-заглушка для анализа без OpenAI."""
    positives = sum(1 for r in reviews if "хорош" in r.lower() or "отличн" in r.lower())
    negatives = sum(1 for r in reviews if "плох" in r.lower() or "ужасн" in r.lower())
    total = len(reviews)
    print(f"Функция-заглушка")
    return (f"Итоговый анализ (заглушка):\n"
            f"Всего отзывов: {total}\n"
            f"Позитивных: {positives}\n"
            f"Негативных: {negatives}\n"
            f"Нейтральных: {total - positives - negatives}")
