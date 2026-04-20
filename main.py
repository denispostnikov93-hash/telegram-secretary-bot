"""
Telegram бот-секретарь
"""
import asyncio
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_ID, TELEGRAM_CHAT_ID
from database import db
from telegram_bot import telegram_bot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_config():
    """Проверить что все необходимые переменные окружения установлены"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        return False
    if not TELEGRAM_ADMIN_ID or TELEGRAM_ADMIN_ID == 0:
        logger.error("❌ TELEGRAM_ADMIN_ID не установлен!")
        return False
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == 0:
        logger.error("❌ TELEGRAM_CHAT_ID не установлен!")
        return False
    return True

async def main():
    logger.info("=" * 60)
    logger.info("🤖 TELEGRAM БОТ-СЕКРЕТАРЬ")
    logger.info("=" * 60)

    if not validate_config():
        logger.error("❌ Конфигурация неполная. Проверь переменные окружения на Railway.")
        return

    try:
        logger.info("📦 Инициализирую БД...")
        await db.init()
        logger.info("✓ БД готова")

        logger.info("📱 Запускаю Telegram бота...")
        logger.info("✓ Напиши /start в боте")
        logger.info("=" * 60)

        await telegram_bot.start()

    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
