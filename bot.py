import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import asyncio

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
WELCOME_IMAGE_URL = os.getenv('WELCOME_IMAGE_URL', 'https://i.ibb.co/tM36RH31/photo-2025-08-22-11-07-10.jpg')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 8000))
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в переменных окружения!")
    exit(1)

logger.info(f"WELCOME_IMAGE_URL: {WELCOME_IMAGE_URL}")
logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
logger.info(f"PORT: {PORT}")
logger.info(f"ADMIN_ID: {ADMIN_ID}")

# Путь к файлу для хранения chat_id групп и каналов
CHATS_FILE = 'chats.json'

def load_chats():
    """Загружаем список чатов из файла"""
    try:
        with open(CHATS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        logger.error("Ошибка чтения chats.json, файл поврежден")
        return {}

def save_chats(chats):
    """Сохраняем список чатов в файл"""
    try:
        with open(CHATS_FILE, 'w') as f:
            json.dump(chats, f, indent=4)
    except Exception as e:
        logger.error(f"Ошибка при сохранении chats.json: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик всех входящих сообщений для сохранения chat_id групп и каналов"""
    if update.message and update.message.chat:
        chat = update.message.chat
        if chat.type in ['group', 'supergroup', 'channel']:
            chats = load_chats()
            chat_id = str(chat.id)
            if chat_id not in chats:
                chats[chat_id] = chat.title or f"Чат {chat_id}"
                save_chats(chats)
                logger.info(f"Добавлен новый чат: {chat.title or chat_id}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    
    # Приветственный текст
    welcome_text = (
        "🌟 Всем привет!  \n\n"
        "Наш новый чат услуг приветствует тебя! "
        "Мы рады будем, если ты будешь находиться в нём.\n\n"
        "✨ Выбери нужный раздел:\n\n"
        "💡 <i>Введи /help для получения дополнительной информации</i>"
    )
    
    # Создаем инлайн кнопки
    keyboard = [
        [InlineKeyboardButton("💎 Чат услуг рай люкс", url="https://t.me/+YCAX1V58SS9mNzAy")],
        [InlineKeyboardButton("⭐ Отзывы рай люкс", url="https://t.me/+kWkpsyHVbZQ2OWMy")],
        [InlineKeyboardButton("📢 Рай люкс канал", url="https://t.me/+UXs_4HwamkljYjI6")],
        [InlineKeyboardButton("📣 Реклама рай люкс", url="https://t.me/+kG38zOCy3x82YzAy")],
        [InlineKeyboardButton("💬 Рай люкс общения", url="https://t.me/+648n00MLjswyMWUy")],
        [InlineKeyboardButton("❓ Справка", callback_data="help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем сообщение с фотографией
    try:
        if WELCOME_IMAGE_URL:
            await update.message.reply_photo(
                photo=WELCOME_IMAGE_URL,
                caption=welcome_text, 
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                welcome_text, 
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке фото: {e}")
        await update.message.reply_text(
            welcome_text, 
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        "🤖 <b>Рай Люкс Бот</b>\n\n"
        "📋 <b>Доступные команды:</b>\n"
        "• /start - Главное меню с ссылками\n"
        "• /help - Справка\n\n"
        "🔗 <b>Наши ресурсы:</b>\n"
        "• Чат услуг - основной чат для заказов\n"
        "• Отзывы - отзывы клиентов о наших услугах\n"
        "• Канал - официальные новости и объявления\n"
        "• Реклама - размещение рекламы\n"
        "• Общение - неформальное общение\n\n"
        "💡 Нажмите на любую кнопку в главном меню для перехода!"
    )
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        try:
            await update.callback_query.message.delete()
            await context.bot.send_message(
                chat_id=update.callback_query.from_user.id,
                text=help_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке справки: {e}")
            try:
                await update.callback_query.edit_message_caption(
                    caption=help_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except:
                await context.bot.send_message(
                    chat_id=update.callback_query.from_user.id,
                    text=help_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на инлайн кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await help_command(update, context)
    elif query.data == "main_menu":
        welcome_text = (
            "🌟 Всем привет! 🌟\n\n"
            "Наш новый чат услуг приветствует тебя! "
            "Мы рады будем, если ты будешь находиться в нём.\n\n"
            "✨ Выбери нужный раздел:\n\n"
            "💡 <i>Введи /help для получения дополнительной информации</i>"
        )
        
        keyboard = [
            [InlineKeyboardButton("💎 Чат услуг рай люкс", url="https://t.me/+YCAX1V58SS9mNzAy")],
            [InlineKeyboardButton("⭐ Отзывы рай люкс", url="https://t.me/+kWkpsyHVbZQ2OWMy")],
            [InlineKeyboardButton("📢 Рай люкс канал", url="https://t.me/+UXs_4HwamkljYjI6")],
            [InlineKeyboardButton("📣 Реклама рай люкс", url="https://t.me/+kG38zOCy3x82YzAy")],
            [InlineKeyboardButton("💬 Рай люкс общения", url="https://t.me/+648n00MLjswyMWUy")],
            [InlineKeyboardButton("❓ Справка", callback_data="help")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            if WELCOME_IMAGE_URL:
                await query.message.delete()
                await context.bot.send_photo(
                    chat_id=query.from_user.id,
                    photo=WELCOME_IMAGE_URL,
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка при отправке главного меню с фото: {e}")
            try:
                await query.edit_message_caption(
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except:
                await context.bot.send_photo(
                    chat_id=query.from_user.id,
                    photo=WELCOME_IMAGE_URL,
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )

async def rek_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /rek для администратора"""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return  # Игнорируем команду, если пользователь не администратор

    # Получаем полный текст сообщения, убирая /rek
    if update.message and update.message.text:
        message_text = update.message.text
        if message_text.startswith('/rek'):
            message_text = message_text[4:].lstrip()  # Убираем /rek и пробелы слева
        else:
            message_text = None
    else:
        message_text = None
    
    if not message_text:
        await update.message.reply_text(
            "📢 Пример использования: /rek Привет, всем!",
            parse_mode='HTML'
        )
        return
    
    try:
        # Загружаем список чатов из файла
        chats = load_chats()
        chat_ids = set(chats.keys())
        
        if not chat_ids:
            await update.message.reply_text(
                "❌ Бот не состоит в группах или каналах, куда можно отправить сообщение.",
                parse_mode='HTML'
            )
            return

        # Список для хранения успешно отправленных чатов
        successful_chats = []
        
        # Отправляем сообщение во все группы и каналы с задержкой, сохраняя точный текст
        for chat_id in chat_ids:
            try:
                await context.bot.send_message(
                    chat_id=int(chat_id),
                    text=message_text  # Без parse_mode для сохранения точного формата
                )
                chat_name = chats[chat_id]
                successful_chats.append(chat_name)
                await asyncio.sleep(0.5)  # Задержка 0.5 секунды между отправками
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения в чат {chat_id}: {e}")
        
        # Формируем сообщение с информацией о чатах
        if successful_chats:
            chats_list = "\n".join([f"• {chat}" for chat in successful_chats])
            await update.message.reply_text(
                f"📢 Рассылка выполнена: '{message_text}'\n\n"
                f"Сообщение отправлено в следующие чаты:\n{chats_list}",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                f"❌ Не удалось отправить сообщение ни в один чат.",
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Ошибка при выполнении рассылки: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при выполнении рассылки: {str(e)}",
            parse_mode='HTML'
        )

# Создаем приложение Telegram
telegram_app = Application.builder().token(BOT_TOKEN).build()

# Добавляем обработчики команд
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(CommandHandler("rek", rek_command))
telegram_app.add_handler(CallbackQueryHandler(button_callback))
telegram_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

if __name__ == '__main__':
    # Если есть WEBHOOK_URL, запускаем вебхук
    if WEBHOOK_URL:
        logger.info("🌐 Запуск в режиме webhook...")
        telegram_app.run_webhook(
            listen='0.0.0.0',
            port=PORT,
            url_path='',
            webhook_url=f"{WEBHOOK_URL}/webhook",
            on_startup=None, # on_startup можно использовать для дополнительных настроек, например, для установки команд бота.
            on_shutdown=None
        )
    else:
        # Режим polling для локального тестирования
        logger.info("🔄 Запуск в режиме polling...")
        telegram_app.run_polling()