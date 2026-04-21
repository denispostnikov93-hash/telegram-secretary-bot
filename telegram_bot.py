"""
Telegram бот-секретарь для приема заявок
"""
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, PRIVACY_POLICY_URL, AGREEMENT_URL
from database import db

logger = logging.getLogger(__name__)

# === STATES ===
class ApplicationForm(StatesGroup):
    waiting_consent_pd = State()
    waiting_consent_policy = State()
    waiting_client_type = State()
    waiting_category = State()
    waiting_name = State()
    waiting_phone = State()
    waiting_description_choice = State()
    waiting_description = State()

# === BOT ===
class TelegramSecretaryBot:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        storage = MemoryStorage()
        self.dp = Dispatcher(storage=storage)
        self.setup_handlers()
        self.user_data = {}

    def setup_handlers(self):
        """Настроить обработчики"""
        # Старт и главное меню
        self.dp.message.register(self.cmd_start, Command("start"))
        self.dp.message.register(self.btn_record, F.text == "📝 Записаться на консультацию")

        # Согласия - высший приоритет, работают в любом состоянии
        self.dp.message.register(self.consent_refusal_handler, F.text.contains("Отказать"))
        self.dp.message.register(self.consent_pd_handler, F.text == "✅ Согласен на обработку персональных данных")
        self.dp.message.register(self.consent_policy_handler, F.text == "✅ Ознакомлен с политикой обработки данных")

        # Тип клиента (с проверкой состояния)
        self.dp.message.register(self.client_type_handler, ApplicationForm.waiting_client_type, F.text.in_(["👤 Физическое лицо", "🏢 Юридическое лицо"]))

        # Категория
        self.dp.message.register(self.category_handler, ApplicationForm.waiting_category)

        # Имя
        self.dp.message.register(self.name_handler, ApplicationForm.waiting_name)

        # Телефон
        self.dp.message.register(self.phone_handler, ApplicationForm.waiting_phone)

        # Описание (выбор)
        self.dp.message.register(self.description_choice_handler, ApplicationForm.waiting_description_choice, F.text.in_(["✏️ Написать", "➡️ Пропустить"]))

        # Описание (текст)
        self.dp.message.register(self.description_handler, ApplicationForm.waiting_description)

        # После отказа - позвонить или дать согласие
        self.dp.message.register(self.phone_refusal_handler, F.text.contains("Позвонить"))
        self.dp.message.register(self.return_consent_handler, F.text.contains("согласие и оставить"))

        # Catch-all для отладки
        self.dp.message.register(self.debug_handler)

    def main_keyboard(self):
        """Главное меню"""
        return types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="📝 Записаться на консультацию")]],
            resize_keyboard=True
        )

    def consent_keyboard(self, consent_pd=False, consent_policy=False):
        """Согласие - динамическая клавиатура"""
        buttons = []
        if not consent_pd:
            buttons.append([types.KeyboardButton(text="✅ Согласен на обработку персональных данных")])
        if not consent_policy:
            buttons.append([types.KeyboardButton(text="✅ Ознакомлен с политикой обработки данных")])
        buttons.append([types.KeyboardButton(text="❌ Отказать в согласии")])

        return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    def client_type_keyboard(self):
        """Выбор типа клиента"""
        return types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="👤 Физическое лицо"), types.KeyboardButton(text="🏢 Юридическое лицо")]],
            resize_keyboard=True
        )

    def category_keyboard_individual(self):
        """Категории для физлиц"""
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="🚗 ДТП")],
                [types.KeyboardButton(text="👨‍👩‍👧 Семейное право")],
                [types.KeyboardButton(text="🏠 Недвижимость")],
                [types.KeyboardButton(text="💼 Трудовые споры")],
                [types.KeyboardButton(text="❓ Другое")]
            ],
            resize_keyboard=True
        )

    def category_keyboard_business(self):
        """Категории для юрлиц"""
        return types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="📋 Регистрация бизнеса")],
                [types.KeyboardButton(text="📝 Договоры и споры")],
                [types.KeyboardButton(text="👷 Трудовые вопросы")],
                [types.KeyboardButton(text="💰 Налоги и штрафы")],
                [types.KeyboardButton(text="❓ Другое")]
            ],
            resize_keyboard=True
        )

    def description_keyboard(self):
        """Выбор: написать или пропустить"""
        return types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="✏️ Написать"), types.KeyboardButton(text="➡️ Пропустить")]],
            resize_keyboard=True
        )

    def validate_phone(self, phone: str) -> bool:
        """Проверить корректность номера телефона"""
        # Удалить пробелы, дефисы, скобки
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)

        # Проверить что это номер телефона (7-15 цифр или +7-15 цифр)
        if re.match(r'^\+?7\d{9,10}$', cleaned) or re.match(r'^\+?\d{10,15}$', cleaned):
            return True
        return False

    async def cmd_start(self, message: types.Message, state: FSMContext):
        """Команда /start"""
        await state.clear()
        user_id = message.from_user.id
        self.user_data[user_id] = {
            'consent_pd': False,
            'consent_policy': False,
            'in_consent_step': False,
            'client_type': None,
            'category': None,
            'name': None,
            'phone': None,
            'description': None
        }

        await message.answer(
            "👋 Добро пожаловать в Правовой центр \"Постников групп\"!\n\n"
            "Мы поможем защитить ваши права. Для записи на консультацию нажмите кнопку.",
            reply_markup=self.main_keyboard()
        )

    async def btn_record(self, message: types.Message, state: FSMContext):
        """Нажата кнопка 'Записаться на консультацию'"""
        user_id = message.from_user.id
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                'consent_pd': False,
                'consent_policy': False,
                'in_consent_step': True
            }

        self.user_data[user_id]['in_consent_step'] = True
        logger.info(f"User {user_id} started application process")

        await message.answer(
            f"Перед подачей заявки ознакомьтесь с документами и подтвердите:\n\n"
            f"📄 Политика обработки данных: {PRIVACY_POLICY_URL}\n"
            f"📄 Согласие на обработку данных: {AGREEMENT_URL}\n\n"
            f"Нажмите обе кнопки ниже для подтверждения:",
            reply_markup=self.consent_keyboard(
                consent_pd=self.user_data[user_id]['consent_pd'],
                consent_policy=self.user_data[user_id]['consent_policy']
            )
        )

    async def consent_pd_handler(self, message: types.Message, state: FSMContext):
        """Согласие на обработку ПД"""
        user_id = message.from_user.id
        logger.info(f"🔵 consent_pd_handler для {user_id}")

        if user_id not in self.user_data:
            self.user_data[user_id] = {'consent_pd': False, 'consent_policy': False, 'in_consent_step': False}
            logger.info(f"   Создан новый user_data для {user_id}")

        in_consent = self.user_data[user_id].get('in_consent_step', False)
        logger.info(f"   in_consent_step={in_consent}")

        if in_consent:
            self.user_data[user_id]['consent_pd'] = True
            logger.info(f"   ✓ Установлен consent_pd=True")
            await self.check_consents(message, state, user_id)
        else:
            logger.warning(f"   ⚠️ in_consent_step=False, пропускаю")

    async def consent_policy_handler(self, message: types.Message, state: FSMContext):
        """Согласие с политикой"""
        user_id = message.from_user.id
        logger.info(f"🟢 consent_policy_handler для {user_id}")

        if user_id not in self.user_data:
            self.user_data[user_id] = {'consent_pd': False, 'consent_policy': False, 'in_consent_step': False}
            logger.info(f"   Создан новый user_data для {user_id}")

        in_consent = self.user_data[user_id].get('in_consent_step', False)
        logger.info(f"   in_consent_step={in_consent}")

        if in_consent:
            self.user_data[user_id]['consent_policy'] = True
            logger.info(f"   ✓ Установлен consent_policy=True")
            await self.check_consents(message, state, user_id)
        else:
            logger.warning(f"   ⚠️ in_consent_step=False, пропускаю")

    async def consent_refusal_handler(self, message: types.Message, state: FSMContext):
        """Обработка отказа от согласия - срабатывает только если пользователь в процессе согласий"""
        user_id = message.from_user.id

        # Защита от duplicate вызовов
        if user_id not in self.user_data or not self.user_data[user_id].get('in_consent_step'):
            logger.info(f"User {user_id} sent refuse button but not in consent step - ignoring")
            return

        logger.info(f"🔴 consent_refusal_handler для {user_id}")

        await self.send_refusal_application(user_id, message.from_user)

        await state.clear()
        self.user_data[user_id] = {}

        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="☎️ Позвонить: 8-495-999-85-89")],
                [types.KeyboardButton(text="↩️ Дать согласие и оставить заявку")]
            ],
            resize_keyboard=True
        )

        await message.answer(
            "😔 Мы уважаем ваше решение и соблюдаем закон о защите персональных данных.\n\n"
            "Без согласия на обработку ПД мы не можем продолжить стандартный процесс консультации.\n\n"
            "Но это не означает, что мы не можем вам помочь! 💪\n\n"
            "Выберите один из вариантов:\n"
            "• Позвоните нам по номеру 8-495-999-85-89 и получите бесплатную консультацию\n"
            "• Или дайте согласие и оставьте заявку через бота",
            reply_markup=keyboard
        )

    async def call_phone_callback(self, query: types.CallbackQuery):
        """Обработка нажатия на кнопку звонка"""
        await query.answer()

    async def phone_refusal_handler(self, message: types.Message, state: FSMContext):
        """Обработка позвонить после отказа"""
        await message.answer(
            "✅ Спасибо! Ждем вашего звонка.\n\n"
            "Наш специалист ответит на все ваши вопросы и поможет найти лучшее решение для вас.",
            reply_markup=self.main_keyboard()
        )

    async def return_consent_handler(self, message: types.Message, state: FSMContext):
        """Вернуться к согласиям"""
        user_id = message.from_user.id

        if user_id not in self.user_data:
            self.user_data[user_id] = {
                'consent_pd': False,
                'consent_policy': False,
                'in_consent_step': True
            }
        else:
            self.user_data[user_id]['consent_pd'] = False
            self.user_data[user_id]['consent_policy'] = False
            self.user_data[user_id]['in_consent_step'] = True

        await message.answer(
            f"Перед подачей заявки ознакомьтесь с документами и подтвердите:\n\n"
            f"📄 Политика обработки данных: {PRIVACY_POLICY_URL}\n"
            f"📄 Согласие на обработку данных: {AGREEMENT_URL}\n\n"
            f"Нажмите обе кнопки ниже для подтверждения:",
            reply_markup=self.consent_keyboard(
                consent_pd=self.user_data[user_id]['consent_pd'],
                consent_policy=self.user_data[user_id]['consent_policy']
            )
        )

    async def send_refusal_application(self, user_id: int, user: types.User = None):
        """Отправить анонимную заявку об отказе в рабочий чат"""
        try:
            # Получить ссылку на Telegram профиль
            profile_link = ""
            if user:
                if user.username:
                    profile_link = f"https://t.me/{user.username}"
                else:
                    profile_link = f"tg://user?id={user.id}"

            message_text = (
                f"⚠️ ОТКАЗ ОТ ОБРАБОТКИ ПЕРСОНАЛЬНЫХ ДАННЫХ\n"
                f"{'━' * 30}\n"
                f"Пользователь отказал в согласии на обработку персональных данных.\n"
                f"Мы соблюдаем законодательство и не собираем данные без согласия.\n"
                f"\n👤 Профиль Telegram: {profile_link}\n"
                f"\n⚠️ ДЕЙСТВИЕ: Позволить пользователю позвонить самостоятельно\n"
                f"на номер 8-495-999-85-89 для консультации.\n"
                f"\n📲 Источник: Telegram\n"
                f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                f"{'━' * 30}"
            )
            await self.bot.send_message(TELEGRAM_CHAT_ID, message_text)
            logger.info(f"✓ Заявка об отказе отправлена в чат")
        except Exception as e:
            logger.error(f"✗ Ошибка отправки заявки об отказе: {e}")

    async def check_consents(self, message: types.Message, state: FSMContext, user_id: int):
        """Проверить оба согласия"""
        consent_pd = self.user_data[user_id].get('consent_pd', False)
        consent_policy = self.user_data[user_id].get('consent_policy', False)

        logger.info(f"⚪ check_consents для {user_id}: PD={consent_pd}, Policy={consent_policy}")

        if consent_pd and consent_policy:
            # Оба согласия получены - переходим к выбору типа клиента
            self.user_data[user_id]['in_consent_step'] = False

            logger.info(f"✅ УСПЕХ: User {user_id} прошел consent step")
            logger.info(f"   Установляю состояние waiting_client_type")

            await state.set_state(ApplicationForm.waiting_client_type)
            current_state = await state.get_state()
            logger.info(f"   Текущее состояние: {current_state}")

            logger.info(f"   Отправляю сообщение с client_type_keyboard")
            await message.answer(
                "✅ Спасибо! Теперь выберите тип клиента:",
                reply_markup=self.client_type_keyboard()
            )
            logger.info(f"   ✓ Сообщение отправлено")
        else:
            # Не все согласия получены
            confirmed_count = 0
            if consent_pd:
                confirmed_count += 1
            if consent_policy:
                confirmed_count += 1

            logger.info(f"User {user_id} has {confirmed_count} confirmations, waiting for more")

            if confirmed_count == 1:
                remaining = []
                if not consent_pd:
                    remaining.append("согласие на обработку персональных данных")
                if not consent_policy:
                    remaining.append("ознакомление с политикой обработки данных")

                await message.answer(
                    f"✅ Отлично! Вы подтвердили 1 из 2 согласий.\n\n"
                    f"Осталось подтвердить:\n"
                    f"✓ {remaining[0]}",
                    reply_markup=self.consent_keyboard(
                        consent_pd=consent_pd,
                        consent_policy=consent_policy
                    )
                )

    async def client_type_handler(self, message: types.Message, state: FSMContext):
        """Выбор типа клиента"""
        user_id = message.from_user.id
        self.user_data[user_id]['client_type'] = message.text.replace("👤 ", "").replace("🏢 ", "")

        await state.set_state(ApplicationForm.waiting_category)

        if "Физическое" in message.text:
            await message.answer("Выберите категорию вопроса:", reply_markup=self.category_keyboard_individual())
        else:
            await message.answer("Выберите категорию вопроса:", reply_markup=self.category_keyboard_business())

    async def category_handler(self, message: types.Message, state: FSMContext):
        """Обработить категорию"""
        user_id = message.from_user.id
        # Убрать эмодзи
        category = message.text.lstrip("🚗👨‍👩‍👧🏠💼📋📝👷💰❓ ")
        self.user_data[user_id]['category'] = category

        await state.set_state(ApplicationForm.waiting_name)
        await message.answer("Как вас зовут?", reply_markup=types.ReplyKeyboardRemove())

    async def name_handler(self, message: types.Message, state: FSMContext):
        """Обработать имя"""
        user_id = message.from_user.id
        self.user_data[user_id]['name'] = message.text

        await state.set_state(ApplicationForm.waiting_phone)
        await message.answer("Ваш номер телефона?")

    async def phone_handler(self, message: types.Message, state: FSMContext):
        """Обработать телефон"""
        user_id = message.from_user.id

        # Проверить корректность номера
        if not self.validate_phone(message.text):
            await message.answer(
                "❌ Пожалуйста, введите корректный номер телефона.\n"
                "Примеры: +7 999 123-45-67 или 79991234567"
            )
            return

        self.user_data[user_id]['phone'] = message.text

        await state.set_state(ApplicationForm.waiting_description_choice)
        await message.answer(
            "Кратко опишите ситуацию (необязательно):",
            reply_markup=self.description_keyboard()
        )

    async def description_choice_handler(self, message: types.Message, state: FSMContext):
        """Выбор: написать или пропустить описание"""
        user_id = message.from_user.id

        if message.text == "✏️ Написать":
            await state.set_state(ApplicationForm.waiting_description)
            await message.answer("Опишите вашу ситуацию:", reply_markup=types.ReplyKeyboardRemove())
        elif message.text == "➡️ Пропустить":
            await self.submit_application(message, state, user_id, description=None)

    async def description_handler(self, message: types.Message, state: FSMContext):
        """Обработать описание"""
        user_id = message.from_user.id
        await self.submit_application(message, state, user_id, description=message.text)

    async def submit_application(self, message: types.Message, state: FSMContext, user_id: int, description=None):
        """Отправить заявку"""
        data = self.user_data[user_id]
        name = data['name']

        # Сохранить в БД
        await db.save_application(
            name=data['name'],
            phone=data['phone'],
            client_type=data['client_type'],
            category=data['category'],
            description=description,
            source="Telegram",
            consent_pd=data['consent_pd'],
            consent_policy=data['consent_policy']
        )

        # Отправить благодарность
        await message.answer(
            f"✅ Спасибо, {name}! Заявка принята.\n"
            f"Наш специалист свяжется с вами в ближайшее время.",
            reply_markup=self.main_keyboard()
        )

        # Отправить в рабочий чат
        await self.send_to_work_chat(data, description, message.from_user)

        # Очистить состояние и данные
        await state.clear()
        if user_id in self.user_data:
            del self.user_data[user_id]

    async def send_to_work_chat(self, data: dict, description: str, user: types.User = None):
        """Отправить заявку в рабочий чат"""
        try:
            # Получить ссылку на Telegram профиль
            profile_link = ""
            if user:
                if user.username:
                    profile_link = f"https://t.me/{user.username}"
                else:
                    profile_link = f"tg://user?id={user.id}"

            message_text = (
                f"🔔 НОВАЯ ЗАЯВКА\n"
                f"{'━' * 30}\n"
                f"👤 Имя: {data['name']}\n"
                f"📱 Телефон: {data['phone']}\n"
                f"🏷️ Тип: {data['client_type']}\n"
                f"📂 Категория: {data['category']}\n"
            )
            if description:
                message_text += f"💬 Суть: {description}\n"

            # Добавить информацию о согласиях
            message_text += (
                f"\n✅ Согласия:\n"
                f"  • Обработка ПД: {'✅ Да' if data['consent_pd'] else '❌ Нет'}\n"
                f"  • Политика обработки: {'✅ Да' if data['consent_policy'] else '❌ Нет'}\n"
            )

            # Добавить ссылку на профиль
            if profile_link:
                message_text += f"\n👤 Профиль Telegram: {profile_link}\n"

            message_text += (
                f"\n📲 Источник: Telegram\n"
                f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                f"{'━' * 30}"
            )
            await self.bot.send_message(TELEGRAM_CHAT_ID, message_text)
            logger.info(f"✓ Заявка отправлена в чат")
        except Exception as e:
            logger.error(f"✗ Ошибка отправки в чат: {e}")

    async def debug_handler(self, message: types.Message, state: FSMContext):
        """Debug обработчик - логирует неожиданные сообщения"""
        user_id = message.from_user.id
        current_state = await state.get_state()
        logger.warning(f"Unhandled message from {user_id}: '{message.text}' in state {current_state}")

    async def start(self):
        """Запустить бота"""
        logger.info("Telegram бот-секретарь запущен и слушает команды")
        await self.dp.start_polling(self.bot)

telegram_bot = TelegramSecretaryBot()
