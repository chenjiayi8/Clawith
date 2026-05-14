"""Generate session titles using the tenant utility LLM model."""

import logging
from uuid import UUID

from sqlalchemy import select

from app.database import async_session
from app.models.chat_session import ChatSession
from app.services.llm import get_model_api_key
from app.services.llm.client import chat_complete

logger = logging.getLogger(__name__)

TITLE_SYSTEM_PROMPT = (
    "Generate a concise title (max 8 words) for this conversation. "
    "Return only the title text, nothing else. No quotes, no punctuation at the end."
)


async def generate_session_title(
    session_id: str,
    user_message: str,
    assistant_response: str,
    utility_model,
    websocket=None,
) -> str | None:
    """Generate a session title and persist it unless the user already edited it."""
    try:
        messages = [
            {"role": "system", "content": TITLE_SYSTEM_PROMPT},
            {"role": "user", "content": user_message[:500]},
            {"role": "assistant", "content": assistant_response[:500]},
            {"role": "user", "content": "Based on this conversation, generate a title."},
        ]

        response = await chat_complete(
            provider=utility_model.provider,
            api_key=get_model_api_key(utility_model),
            model=utility_model.model,
            messages=messages,
            base_url=utility_model.base_url,
            timeout=float(getattr(utility_model, "request_timeout", None) or 120.0),
        )

        raw = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        title = raw.strip().strip('"').strip("'")[:80]
        if not title:
            return None

        async with async_session() as db:
            result = await db.execute(select(ChatSession).where(ChatSession.id == UUID(session_id)))
            session = result.scalar_one_or_none()
            if not session or session.title_edited:
                return None

            session.title = title
            await db.commit()
            logger.info("[SessionTitle] Generated title for %s: %s", session_id, title)

        if websocket:
            try:
                await websocket.send_json(
                    {
                        "type": "session_title_updated",
                        "session_id": session_id,
                        "title": title,
                    }
                )
            except Exception:
                pass

        return title
    except Exception as exc:
        logger.warning("[SessionTitle] Failed to generate title for %s: %s", session_id, exc)
        return None
