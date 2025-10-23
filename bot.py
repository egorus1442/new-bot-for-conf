import os
import re
import uuid
import asyncio
import logging
from typing import Dict, Optional, Any
from dotenv import load_dotenv
import httpx

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler

# Загрузка переменных окружения
load_dotenv()

# Создаём директорию для логов, если её нет
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'bot.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Константы
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_URL = os.getenv('API_URL', 'http://demo.nikta.ai/llm/api/run')
API_LOGIN_URL = 'https://demo.nikta.ai/llm/api/login'
API_EMAIL = 'admin@nikta.ai'
API_PASSWORD = 'lAz32RA9B'
REPORT_CHANNEL_ID = -1003126524033

# Состояния диалога
(CHOOSING_PREDICTION, CHOOSING_SPHERE, WAITING_CUSTOM_SPHERE, WAITING_API_RESPONSE, 
 CHOOSING_ACTION, WAITING_NAME, CHOOSING_CONTACT_TYPE, 
 WAITING_EMAIL, WAITING_PHONE, IN_CHAT_MODE) = range(10)

# Тексты предсказаний
PREDICTIONS = [
    "+40% чистой прибыли",
    "+25% клиентов без рекламы",
    "Минус 30% затрат на персонал",
    "Х2 средний чек",
    "+15 часов в неделю свободы",
    "Рабочий день сокращён на 2 часа",
    "90% рутины исчезло",
    "Все отчёты собираются за 1 клик",
    "Новые рынки открыты для тебя",
    "+300% скорость обработки заказов",
    "Команда стала в 3 раза эффективнее",
    "Лояльность клиентов выросла до 95%"
]

# Сферы бизнеса
SPHERES = [
    "🛍 Ритейл / eCom",
    "🏭 Производство",
    "🧑‍🏫 Образование",
    "🧳 Туризм / Сервисы",
    "💼 IT / Маркетинг",
    "🏗 Другое"
]

# Хранилище данных пользователей
user_data_storage: Dict[int, Dict] = {}


async def get_auth_token() -> str:
    """Получить JWT токен для авторизации в API."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                API_LOGIN_URL,
                json={
                    "email": API_EMAIL,
                    "password": API_PASSWORD
                }
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("token", "")
            if not token:
                logger.error("Token not found in API response")
            return token
    except Exception as e:
        logger.error(f"Error getting auth token: {e}")
        return ""


def get_user_data(user_id: int) -> Dict:
    """Получить данные пользователя."""
    if user_id not in user_data_storage:
        user_data_storage[user_id] = {
            'dialog_id': str(uuid.uuid4()),
            'prediction': None,
            'sphere': None,
            'name': None,
            'contact': None,
            'last_button_message_id': None,
            'messages_to_delete': [],
            'prediction_history': []  # История всех предсказаний и сфер
        }
    return user_data_storage[user_id]


def reset_user_data(user_id: int) -> None:
    """Сбросить данные пользователя при новом /start."""
    if user_id in user_data_storage:
        del user_data_storage[user_id]


def parse_api_response(api_data: Dict[str, Any]) -> list[str]:
    """
    Парсит ответ от внешнего API и возвращает список отдельных сообщений.
    
    Теги <br>...</br> обозначают границы отдельных сообщений.
    """
    if not isinstance(api_data, dict):
        return [str(api_data)]
    
    # Извлекаем поле result
    result = api_data.get('result', '')
    
    if not result:
        # Если result пустой, пробуем другие поля
        if 'response' in api_data:
            result = api_data['response']
        elif 'content' in api_data:
            result = api_data['content']
        elif 'message' in api_data:
            result = api_data['message']
        else:
            return ["Извините, не удалось получить ответ от сервера."]
    
    # Разбиваем на отдельные сообщения по тегам <br>...</br>
    # Паттерн: <br> (любой текст) </br>
    pattern = r'<br\s*/?>\s*(.*?)\s*</br>'
    matches = re.findall(pattern, result, flags=re.IGNORECASE | re.DOTALL)
    
    if not matches:
        # Если паттерн не найден, возвращаем весь текст как одно сообщение
        # Очищаем от возможных одиночных <br> тегов
        result = re.sub(r'<br\s*/?>', '\n', result, flags=re.IGNORECASE)
        result = re.sub(r'</br>', '', result, flags=re.IGNORECASE)
        result = result.strip()
        return [result] if result else []
    
    # Обрабатываем каждое найденное сообщение
    messages = []
    for match in matches:
        # Убираем лишние пробелы и переносы строк в начале и конце
        message = match.strip()
        if message:
            messages.append(message)
    
    return messages


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик команды /start."""
    user_id = update.effective_user.id
    
    # Сброс данных пользователя при новом старте
    reset_user_data(user_id)
    user_data = get_user_data(user_id)
    
    # Сообщение 1
    await update.message.reply_text(
        "Привет!\n"
        "Я — Nikta Oracle, бизнес-оракул от Nikta.ai.\n"
        "За 60 секунд покажу, что ждёт твой бизнес в 2025 — и как сделать это реальностью с помощью автоматизации."
    )
    
    # Ждём 1 секунду
    await asyncio.sleep(1)
    
    # Сообщение 2 с кнопками предсказаний
    keyboard = [[pred] for pred in PREDICTIONS]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    message = await update.message.reply_text(
        "Выбери то, что тебе выпало на карточке 🃏\n"
        "(или просто то, что ты хочешь притянуть в свой бизнес 👇)",
        reply_markup=reply_markup
    )
    
    user_data['last_button_message_id'] = message.message_id
    
    return CHOOSING_PREDICTION


async def handle_prediction_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора предсказания."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    text = update.message.text
    
    # Проверяем, что пользователь нажал на кнопку из списка
    if text not in PREDICTIONS:
        # Сохраняем ID сообщения для последующего удаления
        user_data['messages_to_delete'].append(update.message.message_id)
        msg = await update.message.reply_text(
            "Пожалуйста, выберите один из вариантов, нажав на кнопку 👇"
        )
        user_data['messages_to_delete'].append(msg.message_id)
        return CHOOSING_PREDICTION
    
    # Удаляем сообщение пользователя и предыдущие некорректные сообщения
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        if user_data['last_button_message_id']:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_data['last_button_message_id'])
        for msg_id in user_data['messages_to_delete']:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
            except:
                pass
        user_data['messages_to_delete'] = []
    except Exception as e:
        logger.error(f"Error deleting messages: {e}")
    
    user_data['prediction'] = text
    
    # Сообщение 3 с выбором сферы
    keyboard = [[sphere] for sphere in SPHERES]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    message = await update.message.reply_text(
        "Отличный выбор 😎\n"
        "Проверим, насколько твоё предсказание реально.\n"
        "В какой сфере работает твой бизнес? 👇",
        reply_markup=reply_markup
    )
    
    user_data['last_button_message_id'] = message.message_id
    
    return CHOOSING_SPHERE


async def handle_sphere_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора сферы бизнеса."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    text = update.message.text
    
    # Проверяем, что пользователь нажал на кнопку из списка
    if text not in SPHERES:
        user_data['messages_to_delete'].append(update.message.message_id)
        msg = await update.message.reply_text(
            "Пожалуйста, выберите одну из сфер, нажав на кнопку 👇"
        )
        user_data['messages_to_delete'].append(msg.message_id)
        return CHOOSING_SPHERE
    
    # Удаляем сообщение пользователя и предыдущие некорректные сообщения
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        if user_data['last_button_message_id']:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_data['last_button_message_id'])
        for msg_id in user_data['messages_to_delete']:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
            except:
                pass
        user_data['messages_to_delete'] = []
        user_data['last_button_message_id'] = None
    except Exception as e:
        logger.error(f"Error deleting messages: {e}")
    
    # Если выбрано "Другое", запрашиваем кастомную сферу
    if text == "🏗 Другое":
        await update.message.reply_text(
            "Напиши в сообщении сферу, в которой работает твой бизнес",
            reply_markup=ReplyKeyboardRemove()
        )
        return WAITING_CUSTOM_SPHERE
    
    user_data['sphere'] = text
    
    # Сохраняем в историю текущее предсказание и сферу
    user_data['prediction_history'].append({
        'prediction': user_data['prediction'],
        'sphere': user_data['sphere']
    })
    
    # Формируем запрос к API
    await send_api_request(update, context, user_data)
    
    return IN_CHAT_MODE


async def handle_custom_sphere(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик ввода кастомной сферы бизнеса."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    # Сохраняем введенную сферу
    user_data['sphere'] = update.message.text.strip()
    
    # Сохраняем в историю текущее предсказание и сферу
    user_data['prediction_history'].append({
        'prediction': user_data['prediction'],
        'sphere': user_data['sphere']
    })
    
    # Формируем запрос к API
    await send_api_request(update, context, user_data)
    
    return IN_CHAT_MODE


async def send_api_request(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data: Dict, user_message: Optional[str] = None) -> None:
    """Отправка запроса к внешнему API."""
    # Получаем токен авторизации
    auth_token = await get_auth_token()
    if not auth_token:
        await update.message.reply_text(
            "Извините, произошла ошибка авторизации. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    # Формируем контент для API
    if user_message is None:
        # Первый запрос с предсказанием и сферой
        content = f"Предсказание: {user_data['prediction']}, Сфера: {user_data['sphere']}"
    else:
        # Последующие сообщения от пользователя
        content = user_message
    
    payload = {
        "scenario_id": "conf-bot",
        "state": {
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ]
        },
        "channel_id": "1",
        "dialog_id": user_data['dialog_id'],
        "llm_model": "anthropic/claude-sonnet-4"
    }
    
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(API_URL, json=payload, headers=headers)
            response.raise_for_status()
            
            # Получаем ответ от API
            api_response = response.json()
            logger.info(f"API response: {api_response}")
            
            # Парсим ответ и получаем список отдельных сообщений
            messages = parse_api_response(api_response)
            
            # Отправляем каждое сообщение отдельно
            for i, message_text in enumerate(messages):
                if i > 0:
                    # Небольшая задержка между сообщениями для лучшего UX
                    await asyncio.sleep(0.5)
                
                # Последнее сообщение отправляем с удалением клавиатуры
                if i == len(messages) - 1:
                    await update.message.reply_text(message_text, reply_markup=ReplyKeyboardRemove())
                else:
                    await update.message.reply_text(message_text)
            
            # Если это первый ответ от API, показываем кнопки действий
            if user_message is None:
                await asyncio.sleep(1)
                await show_action_buttons(update, context, user_data)
        
    except httpx.HTTPError as e:
        logger.error(f"API request error: {e}")
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке запроса. Попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )


async def show_action_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data: Dict) -> None:
    """Показать кнопки выбора дальнейшего действия."""
    keyboard = [
        ["🔍 Хочу такой анализ для своего бизнеса"],
        ["🔁 Посмотреть другое предсказание"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    message = await update.message.reply_text(
        "Выбери дальнейшее действие",
        reply_markup=reply_markup
    )
    
    user_data['last_button_message_id'] = message.message_id


async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик сообщений в режиме чата с API."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    text = update.message.text
    
    # Проверяем, не нажал ли пользователь на кнопку действия
    if text == "🔍 Хочу такой анализ для своего бизнеса":
        return await handle_analysis_request(update, context)
    elif text == "🔁 Посмотреть другое предсказание":
        return await handle_restart(update, context)
    
    # Если есть активные кнопки, просим нажать на них
    if user_data['last_button_message_id']:
        user_data['messages_to_delete'].append(update.message.message_id)
        msg = await update.message.reply_text(
            "Пожалуйста, выберите один из вариантов, нажав на кнопку 👇"
        )
        user_data['messages_to_delete'].append(msg.message_id)
        return IN_CHAT_MODE
    
    # Отправляем сообщение в API
    await send_api_request(update, context, user_data, text)
    
    return IN_CHAT_MODE


async def handle_analysis_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик запроса на анализ бизнеса."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    # Удаляем сообщение с кнопкой и сообщение пользователя
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        if user_data['last_button_message_id']:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_data['last_button_message_id'])
        for msg_id in user_data['messages_to_delete']:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
            except:
                pass
        user_data['messages_to_delete'] = []
        user_data['last_button_message_id'] = None
    except Exception as e:
        logger.error(f"Error deleting messages: {e}")
    
    # Сообщение 6
    await update.message.reply_text(
        "Круто 💪\n"
        "Я соберу для тебя персональный отчёт, где покажу реальные точки роста твоей компании.\n"
        "Напиши, как к тебе обращаться 👇",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return WAITING_NAME


async def handle_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик перезапуска с новым предсказанием."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    # Удаляем сообщение с кнопкой и сообщение пользователя
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        if user_data['last_button_message_id']:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_data['last_button_message_id'])
        for msg_id in user_data['messages_to_delete']:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
            except:
                pass
        user_data['messages_to_delete'] = []
    except Exception as e:
        logger.error(f"Error deleting messages: {e}")
    
    # Генерируем новый dialog_id
    user_data['dialog_id'] = str(uuid.uuid4())
    user_data['prediction'] = None
    user_data['sphere'] = None
    
    # Показываем кнопки выбора предсказания
    keyboard = [[pred] for pred in PREDICTIONS]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    message = await update.message.reply_text(
        "Выбери то, что тебе выпало на карточке 🃏\n"
        "(или просто то, что ты хочешь притянуть в свой бизнес 👇)",
        reply_markup=reply_markup
    )
    
    user_data['last_button_message_id'] = message.message_id
    
    return CHOOSING_PREDICTION


async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик ввода имени."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    user_data['name'] = update.message.text
    
    # Сообщение 7
    keyboard = [
        ["📱 Отправить номер"],
        ["📧 Указать e-mail"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    message = await update.message.reply_text(
        "Отлично!\n"
        "Куда прислать результат?\n"
        "Отправляя свои контактные данные, вы соглашаетесь на обработку данных согласно политике Nikta.ai",
        reply_markup=reply_markup
    )
    
    user_data['last_button_message_id'] = message.message_id
    
    return CHOOSING_CONTACT_TYPE


async def handle_contact_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора типа контакта."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    text = update.message.text
    
    if text not in ["📱 Отправить номер", "📧 Указать e-mail"]:
        user_data['messages_to_delete'].append(update.message.message_id)
        msg = await update.message.reply_text(
            "Пожалуйста, выберите один из вариантов, нажав на кнопку 👇"
        )
        user_data['messages_to_delete'].append(msg.message_id)
        return CHOOSING_CONTACT_TYPE
    
    # Удаляем сообщение пользователя и предыдущие некорректные сообщения
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        if user_data['last_button_message_id']:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=user_data['last_button_message_id'])
        for msg_id in user_data['messages_to_delete']:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
            except:
                pass
        user_data['messages_to_delete'] = []
        user_data['last_button_message_id'] = None
    except Exception as e:
        logger.error(f"Error deleting messages: {e}")
    
    if text == "📱 Отправить номер":
        # Запрашиваем номер телефона
        keyboard = [[KeyboardButton("📱 Отправить мой номер", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            "Нажмите на кнопку ниже, чтобы отправить свой номер телефона 👇",
            reply_markup=reply_markup
        )
        
        return WAITING_PHONE
    else:
        # Запрашиваем email
        await update.message.reply_text(
            "Отправь свой e-mail",
            reply_markup=ReplyKeyboardRemove()
        )
        
        return WAITING_EMAIL


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик получения номера телефона."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    if update.message.contact:
        phone = update.message.contact.phone_number
        user_data['contact'] = f"Телефон: {phone}"
        
        await send_final_message(update, context)
        
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопку для отправки номера телефона 👇"
        )
        return WAITING_PHONE


async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик получения email."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    email = update.message.text.strip()
    
    # Простая валидация email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        await update.message.reply_text(
            "Введите пожалуйста e-mail корректно"
        )
        return WAITING_EMAIL
    
    user_data['contact'] = f"Email: {email}"
    
    await send_final_message(update, context)
    
    return ConversationHandler.END


async def send_report_to_channel(context: ContextTypes.DEFAULT_TYPE, user_data: Dict, user: Any) -> None:
    """Отправка отчета в канал."""
    try:
        # Формируем отчетное сообщение
        report_lines = [
            "📊 <b>Новая заявка от пользователя</b>",
            "",
            f"👤 <b>Имя:</b> {user_data['name']}",
            f"📞 <b>Контакт:</b> {user_data['contact']}",
            f"🆔 <b>Telegram ID:</b> {user.id}",
            f"👨‍💼 <b>Username:</b> @{user.username if user.username else 'не указан'}",
            "",
            "<b>📈 История предсказаний:</b>"
        ]
        
        # Добавляем все предсказания из истории
        for i, entry in enumerate(user_data['prediction_history'], 1):
            report_lines.append(f"\n<b>Попытка {i}:</b>")
            report_lines.append(f"🔮 Предсказание: {entry['prediction']}")
            report_lines.append(f"🏢 Сфера: {entry['sphere']}")
        
        report_text = "\n".join(report_lines)
        
        # Отправляем отчет в канал
        await context.bot.send_message(
            chat_id=REPORT_CHANNEL_ID,
            text=report_text,
            parse_mode='HTML'
        )
        logger.info(f"Report sent to channel for user {user.id}")
    except Exception as e:
        logger.error(f"Error sending report to channel: {e}")


async def send_final_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправка финального сообщения."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    # Отправляем отчет в канал
    await send_report_to_channel(context, user_data, update.effective_user)
    
    # Сообщение 8
    await update.message.reply_text(
        "🎯 Готово!\n"
        "Твоя заявка передана в штаб Nikta.ai 🚀\n"
        "А пока - загляни:\n"
        "🌐 nikta.ai - посмотри, как другие компании уже подтвердили свои предсказания.\n"
        "💬 @nikta_ai - наш Telegram-канал с кейсами и свежими идеями.",
        reply_markup=ReplyKeyboardRemove(),
        disable_web_page_preview=True
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена диалога."""
    await update.message.reply_text(
        "Диалог отменён. Используйте /start для начала.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main() -> None:
    """Запуск бота."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    # Создаём приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Создаём ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_PREDICTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prediction_choice)
            ],
            CHOOSING_SPHERE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sphere_choice)
            ],
            WAITING_CUSTOM_SPHERE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_sphere)
            ],
            IN_CHAT_MODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_message)
            ],
            WAITING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)
            ],
            CHOOSING_CONTACT_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact_type)
            ],
            WAITING_PHONE: [
                MessageHandler(filters.CONTACT, handle_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
            ],
            WAITING_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start)
        ],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    # Запускаем бота
    logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

