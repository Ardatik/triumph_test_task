import logging
import os

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def send_telegram_notification(chat_id: str) -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN не задан, уведомление не отправлено")
        return
    logger.info("Пытаюсь отправить уведомление")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "Отчёт готов.",
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10.0)
            if resp.status_code == 200:
                logger.info("Уведомление отправлено пользователю")
            else:
                logger.warning(
                    "Ошибка отправки уведомления: %d %s",
                    resp.status_code,
                    resp.text,
                )
    except Exception as exc:
        logger.error("Исключение при отправке уведомления: %s", exc)
