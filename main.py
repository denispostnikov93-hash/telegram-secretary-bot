"""
Telegram бот-секретарь
"""
import asyncio
import logging
from database import db
from telegram_bot import telegram_bot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("=" * 60)
    logger.info("🤖 TELEGRAM БОТ-СЕКРЕТАРЬ")
    logger.info("=" * 60)

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
