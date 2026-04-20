"""
Конфиг для бота-секретаря
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ===== TELEGRAM =====
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_ADMIN_ID = int(os.getenv('TELEGRAM_ADMIN_ID', '0')) if os.getenv('TELEGRAM_ADMIN_ID', '0').isdigit() else 0
TELEGRAM_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID', '0')) if os.getenv('TELEGRAM_CHAT_ID', '0').lstrip('-').isdigit() else 0

# ===== DATABASE =====
DATABASE_PATH = os.getenv('DATABASE_PATH', 'applications.db')

# ===== LINKS =====
PRIVACY_POLICY_URL = "https://postnikov.group/privacy-policy"
AGREEMENT_URL = "https://postnikov.group/agreement"

# ===== DEBUG =====
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
