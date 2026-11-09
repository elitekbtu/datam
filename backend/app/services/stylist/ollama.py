import httpx

from app.services.errors import ServiceUnavailable
from core.config import settings


async def chat_json(system: str, messages: list[dict[str, str]]) -> str:
    body = {
        "model": settings.OLLAMA_MODEL,
        "stream": False,
        "think": False,
        "format": "json",
        "keep_alive": "10m",
        "options": {"temperature": 0.3, "num_predict": 1200},
        "messages": [{"role": "system", "content": system}, *messages],
    }
    try:
        async with httpx.AsyncClient(
            base_url=settings.OLLAMA_URL, timeout=settings.OLLAMA_TIMEOUT_SECONDS
        ) as client:
            response = await client.post("/api/chat", json=body)
    except httpx.TimeoutException as exc:
        raise ServiceUnavailable("The AI stylist took too long to answer") from exc
    except httpx.HTTPError as exc:
        raise ServiceUnavailable("The AI stylist is offline") from exc

    if response.status_code == httpx.codes.NOT_FOUND:
        raise ServiceUnavailable(f"Model {settings.OLLAMA_MODEL} is not pulled in Ollama")
    if response.is_error:
        raise ServiceUnavailable("The AI stylist failed to answer")
    try:
        data = response.json()
        message = data.get("message") if isinstance(data, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Missing message content")
    except ValueError as exc:
        raise ServiceUnavailable("Стилист вернул некорректный ответ. Попробуйте ещё раз.") from exc
    return content
