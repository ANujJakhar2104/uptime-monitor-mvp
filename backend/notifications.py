import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Change 'str | None' to 'Optional[str]'
async def send_webhook(webhook_url: Optional[str], payload: dict) -> None:
    if not webhook_url:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=payload, timeout=5.0)
    except httpx.RequestError as exc:
        logger.warning(f"Webhook delivery failed for {webhook_url}: {exc}")
