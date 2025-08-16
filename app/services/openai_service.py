import httpx
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.core import settings
from app.database.session import get_db # get_db is already async
from app.models import Promt


async def analyze_reviews(
    reviewsBlock: List[str],
    promt_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db) # This will now correctly inject an AsyncSession
) -> str:    
    # if 1==1: # Keeping the placeholder logic as it was, but commenting out for actual run
    #     return "OOOOOOOOOOOOOOOOOOOOOOOOO."

    if not settings.OPENAI_API_KEY:
        # Consider raising an HTTPException or logging a warning if key is missing in production
        return "ИИ-ключ не указан. Анализ не может быть выполнен. Используется заглушка."

    titlePromt = "Проанализируй отзывы"
    if promt_id:
        stmt = select(Promt).filter(Promt.id == promt_id)
        result = await db.execute(stmt)
        promt = result.scalar_one_or_none()
        if promt and promt.description:
            titlePromt = f"{promt.description.strip()}"

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    userReviews = "Отзывы пользователей:"
    # Ensure reviewsBlock is a string representation suitable for the prompt
    reviews_str = "\n".join(map(str, reviewsBlock)) # Example: join list of strings
    promtRreviews = f"{titlePromt}\n{userReviews}\n{reviews_str}"


    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": [{"role": "user", "content": promtRreviews}],
        "temperature": 0.7, # Consider making this configurable
    }

    try:
        async with httpx.AsyncClient(timeout=settings.OPENAI_TIMEOUT if hasattr(settings, 'OPENAI_TIMEOUT') else 30.0) as client: # Configurable timeout
            response = await client.post(f"{settings.OPENAI_API_BASE}/chat/completions", headers=headers, json=payload)

            if response.status_code != 200:
                error_text = await response.aread()
                # Log the detailed error for backend visibility
                print(f"❌ Ошибка от OpenAI: {response.status_code} {error_text.decode()}")
                # Provide a more generic error to the client
                raise HTTPException(status_code=response.status_code, detail="Ошибка при обращении к ИИ-сервису.")

            data = response.json()
            if "choices" in data and len(data["choices"]) > 0 and "message" in data["choices"][0] and "content" in data["choices"][0]["message"]:
                return data["choices"][0]["message"]["content"]
            else:
                # Log unexpected response structure
                print(f"❌ Неожиданный формат ответа от OpenAI: {data}")
                raise HTTPException(status_code=500, detail="Неожиданный формат ответа от ИИ-сервиса.")

    except httpx.TimeoutException:
        print(f"⏳ Таймаут при обращении к ИИ-сервису: {settings.OPENAI_API_BASE}")
        raise HTTPException(status_code=504, detail="Таймаут при обращении к ИИ-сервису. Попробуйте позже.")
    except httpx.HTTPStatusError as e: # Specific HTTP errors from httpx
        error_content = await e.response.aread()
        print(f"🚨 HTTP ошибка: {e.response.status_code} {error_content.decode()}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Ошибка HTTP ({e.response.status_code}) при обращении к ИИ-сервису.")
    except Exception as e: # Catch other exceptions, including potential JSON parsing errors if response is not JSON
        print(f"⚡ Общая ошибка при работе с ИИ: {str(e)}")
        # Avoid exposing internal error details directly to the client
        raise HTTPException(status_code=500, detail="Внутренняя ошибка при работе с ИИ-сервисом. Попробуйте позже.")


# fake_analysis can remain as a synchronous utility function if needed for other purposes
# or if it's purely a CPU-bound operation not involving I/O.
def fake_analysis(reviews: List[str]) -> str:
    """Функция-заглушка для анализа без OpenAI."""
    positives = sum(1 for r in reviews if "хорош" in r.lower() or "отличн" in r.lower())
    negatives = sum(1 for r in reviews if "плох" in r.lower() or "ужасн" in r.lower())
    total = len(reviews)
    print(f"Функция-заглушка (синхронная)")
    return (f"Итоговый анализ (заглушка):\n"
            f"Всего отзывов: {total}\n"
            f"Позитивных: {positives}\n"
            f"Негативных: {negatives}\n"
            f"Нейтральных: {total - positives - negatives}")
