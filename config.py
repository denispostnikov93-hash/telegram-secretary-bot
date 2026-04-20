"""
Конфиг для бота-секретаря
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ===== TELEGRAM =====
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не установлен в переменных окружения!")

TELEGRAM_ADMIN_ID_STR = os.getenv('TELEGRAM_ADMIN_ID')
if not TELEGRAM_ADMIN_ID_STR:
    raise ValueError("❌ TELEGRAM_ADMIN_ID не установлен в переменных окружения!")
TELEGRAM_ADMIN_ID = int(TELEGRAM_ADMIN_ID_STR)

TELEGRAM_CHAT_ID_STR = os.getenv('TELEGRAM_CHAT_ID')
if not TELEGRAM_CHAT_ID_STR:
    raise ValueError("❌ TELEGRAM_CHAT_ID не установлен в переменных окружения!")
TELEGRAM_CHAT_ID = int(TELEGRAM_CHAT_ID_STR)

# ===== DATABASE =====
DATABASE_PATH = os.getenv('DATABASE_PATH', 'applications.db')

# ===== LINKS =====
PRIVACY_POLICY_URL = "https://postnikov.group/privacy-policy"
AGREEMENT_URL = "https://postnikov.group/agreement"

# ===== DEBUG =====
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
