import telebot
import secrets
import time
import os
from flask import Flask, request, render_template, redirect, url_for
import threading

# --- Конфигурация ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEB_SERVER_HOST = os.environ.get("WEB_SERVER_HOST", "0.0.0.0")
WEB_SERVER_PORT = int(os.environ.get("WEB_SERVER_PORT", 5000))
CODE_EXPIRATION_TIME = int(os.environ.get("CODE_EXPIRATION_TIME", 60 * 10)) # 10 минут
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID") # ID чата админа.  Установите вручную после первого запуска.
if ADMIN_CHAT_ID:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)

# --- Инициализация ---
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- Хранилище данных (замените на БД в production) ---
user_codes = {}  # {user_id: {"code": "...", "timestamp": time.time()}}
used_codes = set()
user_data = {}  # {user_id: {"username": ..., "first_name": ..., "last_name": ..., "approved": True/False, "resources": ["resource1", "resource2"]}}
pending_requests = {} # {user_id: message_id} - ID сообщения с запросом, чтобы админ мог его отредактировать

# --- Управление ресурсами (замените на более сложную логику) ---
RESOURCE_LIST = ["resource1", "resource2", "resource3"]  # Список доступных ресурсов

# --- Функции ---

def generate_code():
    """Генерирует безопасный случайный код."""
    return secrets.token_hex(16)

def is_code_valid(code):
    """Проверяет, является ли код валидным и не истек ли срок его действия."""
    if code in used_codes:
        return False, None

    for user_id, data in user_codes.items():
        if data["code"] == code:
            if (time.time() - data["timestamp"]) <= CODE_EXPIRATION_TIME:
                return True, user_id
            else:
                del user_codes[user_id]
                return False, None
    return False, None

def is_admin(user_id):
    """Проверяет, является ли пользователь администратором."""
    return user_id == ADMIN_CHAT_ID

def is_approved(user_id):
    """Проверяет, одобрен ли пользователь."""
    return user_id in user_data and user_data[user_id].get("approved", False)

def get_user_resources(user_id):
    """Возвращает список ресурсов, к которым у пользователя есть доступ."""
    if user_id in user_data:
        return user_data[user_id].get("resources", [])
    return []

# --- Обработчики Telegram Bot ---

@bot.message_handler(commands=['start'])
def start(message):
    """Обрабатывает команду /start."""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    if not user_data:  # Первый пользователь становится админом
        global ADMIN_CHAT_ID
        ADMIN_CHAT_ID = user_id
        user_data[user_id] = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "approved": True,  # Админ автоматически одобрен
            "resources": RESOURCE_LIST.copy()  # Доступ ко всем ресурсам
        }
        bot.reply_to(message, "Вы назначены администратором бота.")
        #Сохраняем ID админа в переменные среды (можно и в файл, главное сохранить)
        os.environ["ADMIN_CHAT_ID"] = str(ADMIN_CHAT_ID)
        print(f"ADMIN_CHAT_ID установлен в {ADMIN_CHAT_ID}.  Пожалуйста, перезапустите контейнер, чтобы это значение вступило в силу.")

    elif user_id not in user_data: #Новый пользователь
        user_data[user_id] = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "approved": False,
            "resources": []
        }

        # Отправляем запрос на одобрение админу
        markup = telebot.types.InlineKeyboardMarkup()
        approve_button = telebot.types.InlineKeyboardButton("Одобрить", callback_data=f"approve_{user_id}")
        decline_button = telebot.types.InlineKeyboardButton("Отклонить", callback_data=f"decline_{user_id}")
        markup.add(approve_button, decline_button)

        request_message = bot.send_message(ADMIN_CHAT_ID, f"Запрос на одобрение нового пользователя:\nID: {user_id}\nИмя: {first_name}\nUsername: @{username}", reply_markup=markup)
        pending_requests[user_id] = request_message.message_id
        bot.reply_to(message, "Ваш запрос отправлен администратору на рассмотрение.  Пожалуйста, подождите.")
    else:
        bot.reply_to(message, "Вы уже зарегистрированы. Ожидайте одобрения администратора.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("decline_"))
def handle_approval(call):
    """Обрабатывает нажатия кнопок одобрения/отклонения."""
    user_id = int(call.data.split("_")[1])
    chat_id = call.message.chat.id

    if not is_admin(chat_id):
        bot.answer_callback_query(call.id, "У вас нет прав администратора.")
        return

    if call.data.startswith("approve_"):
        user_data[user_id]["approved"] = True
        bot.send_message(user_id, "Ваша заявка одобрена администратором! Теперь вы можете получать коды.")
        bot.edit_message_text(f"Пользователь {user_id} одобрен.", chat_id=chat_id, message_id=pending_requests.get(user_id)) #Редактируем сообщение админу
        del pending_requests[user_id]

    else:
        del user_data[user_id] #Удаляем пользователя
        bot.send_message(user_id, "Ваша заявка отклонена администратором.")
        bot.edit_message_text(f"Пользователь {user_id} отклонен.", chat_id=chat_id, message_id=pending_requests.get(user_id)) #Редактируем сообщение админу
        del pending_requests[user_id]
    bot.answer_callback_query(call.id, "Действие выполнено.")

@bot.message_handler(commands=['getcode'])
def get_code(message):
    """Генерирует и отправляет код пользователю, если он одобрен."""
    user_id = message.from_user.id

    if not is_approved(user_id):
        bot.reply_to(message, "Вы не одобрены администратором.  Обратитесь к нему для получения доступа.")
        return

    if not get_user_resources(user_id):
        bot.reply_to(message, "У вас нет доступа ни к одному ресурсу.")
        return

    code = generate_code()
    user_codes[user_id] = {"code": code, "timestamp": time.time()}
    bot.reply_to(message, f"Твой код: {code}. Он действует {CODE_EXPIRATION_TIME // 60} минут.")
    print(f"Сгенерирован код {code} для пользователя {user_id}")

@bot.message_handler(commands=['resources'])
def list_resources(message):
    """Показывает пользователю, к каким ресурсам у него есть доступ."""
    user_id = message.from_user.id

    if not is_approved(user_id):
        bot.reply_to(message, "Вы не одобрены администратором.")
        return

    resources = get_user_resources(user_id)
    if resources:
        bot.reply_to(message, f"У вас есть доступ к следующим ресурсам: {', '.join(resources)}")
    else:
        bot.reply_to(message, "У вас нет доступа ни к одному ресурсу.")

@bot.message_handler(commands=['manage']) #Команда для админа
def manage_user_resources(message):
     """Позволяет админу управлять ресурсами пользователя."""
     user_id = message.from_user.id

     if not is_admin(user_id):
         bot.reply_to(message, "У вас нет прав администратора.")
         return

     try:
        parts = message.text.split()
        target_user_id = int(parts[1])  # ID пользователя, которым нужно управлять
        action = parts[2]  # "add" или "remove"
        resource = parts[3]  # Название ресурса
     except (IndexError, ValueError):
         bot.reply_to(message, "Использование: /manage <user_id> <add/remove> <resource>")
         return

     if target_user_id not in user_data:
         bot.reply_to(message, "Пользователь не найден.")
         return

     if resource not in RESOURCE_LIST:
         bot.reply_to(message, "Ресурс не найден.")
         return

     if action == "add":
         if resource not in user_data[target_user_id]["resources"]:
            user_data[target_user_id]["resources"].append(resource)
            bot.reply_to(message, f"Ресурс '{resource}' добавлен пользователю {target_user_id}.")
         else:
            bot.reply_to(message, f"У пользователя {target_user_id} уже есть доступ к ресурсу '{resource}'.")

     elif action == "remove":
         if resource in user_data[target_user_id]["resources"]:
             user_data[target_user_id]["resources"].remove(resource)
             bot.reply_to(message, f"Ресурс '{resource}' удален у пользователя {target_user_id}.")
         else:
            bot.reply_to(message, f"У пользователя {target_user_id} нет доступа к ресурсу '{resource}'.")
     else:
         bot.reply_to(message, "Неверное действие. Используйте 'add' или 'remove'.")

# --- Запуск ---

def run_bot():
    bot.infinity_polling()

