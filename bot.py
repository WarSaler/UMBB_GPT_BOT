#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UMBB GPT Telegram Bot
С обработкой ошибок импорта и fallback на HTTP сервер
"""

import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs

# Логирование
try:
    from loguru import logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Попытка импорта telegram модулей
TELEGRAM_AVAILABLE = False
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
    TELEGRAM_AVAILABLE = True
    logger.info("✅ Telegram модули успешно импортированы")
except ImportError as e:
    logger.warning(f"❌ telegram модуль недоступен: {e}")
    logger.info("🔄 Работаем в режиме простого HTTP сервера")

# Загрузка переменных окружения
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv не найден, используем системные переменные")

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 10000))

class SimpleHandler(BaseHTTPRequestHandler):
    """HTTP обработчик для fallback режима"""
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            status = "✅ Telegram бот активен" if TELEGRAM_AVAILABLE and BOT_TOKEN else "⚠️ HTTP сервер (fallback)"
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>UMBB Bot Server</title>
                <meta charset="utf-8">
            </head>
            <body>
                <h1>🤖 UMBB Bot Server</h1>
                <p>{status}</p>
                <p>🐍 Python: {sys.version}</p>
                <p>📁 Директория: {os.getcwd()}</p>
                <p>🔧 Telegram доступен: {TELEGRAM_AVAILABLE}</p>
                <p>🔑 Bot Token: {'✅ Настроен' if BOT_TOKEN else '❌ Отсутствует'}</p>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")

# Telegram bot функции
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    welcome_text = """
🤖 Привет! Я UMBB GPT Bot!

📝 Отправь мне текст - я отвечу через GPT
🖼️ Отправь изображение - я его обработаю
❓ /help - показать все команды
    """
    
    keyboard = [
        [InlineKeyboardButton("📝 Текстовый запрос", callback_data="text_mode")],
        [InlineKeyboardButton("🖼️ Обработка изображений", callback_data="image_mode")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
🤖 UMBB GPT Bot - Команды:

/start - Главное меню
/help - Эта справка

📝 Текстовые сообщения:
• Просто напиши мне что-нибудь
• Я отвечу через GPT

🖼️ Изображения:
• Отправь фото
• Я опишу что на нем
    """
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_text = update.message.text
    user_name = update.effective_user.first_name or "Пользователь"
    
    # Простой ответ (без OpenAI пока)
    response = f"Привет, {user_name}! Ты написал: '{user_text}'\n\n🤖 Скоро здесь будет GPT ответ!"
    
    await update.message.reply_text(response)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка изображений"""
    await update.message.reply_text("🖼️ Получил изображение! Скоро добавлю обработку через GPT Vision.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "text_mode":
        await query.edit_message_text("📝 Режим текста активен! Просто напиши мне что-нибудь.")
    elif query.data == "image_mode":
        await query.edit_message_text("🖼️ Режим изображений активен! Отправь мне фото.")
    elif query.data == "help":
        await help_command(query, context)

def run_telegram_bot():
    """Запуск Telegram бота"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден в переменных окружения")
        return False
    
    try:
        # Создание приложения
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Добавление обработчиков
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_handler(CallbackQueryHandler(button_callback))
        
        logger.info("🚀 Запуск Telegram бота...")
        
        # Запуск с webhook для Render
        if os.getenv('RENDER'):
            # Webhook режим для Render
            app.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                webhook_url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}"
            )
        else:
            # Polling режим для локальной разработки
            app.run_polling()
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска Telegram бота: {e}")
        return False

def run_http_server():
    """Запуск HTTP сервера (fallback)"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), SimpleHandler)
        logger.info(f"🌐 HTTP сервер запущен на порту {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Ошибка HTTP сервера: {e}")

def main():
    """Главная функция"""
    logger.info("🚀 Запуск UMBB Bot...")
    logger.info(f"🐍 Python версия: {sys.version}")
    logger.info(f"📁 Рабочая директория: {os.getcwd()}")
    
    # Попытка запуска Telegram бота
    if TELEGRAM_AVAILABLE:
        logger.info("🤖 Попытка запуска Telegram бота...")
        if run_telegram_bot():
            return
    
    # Fallback на HTTP сервер
    logger.info("🔄 Запуск в режиме HTTP сервера")
    run_http_server()

if __name__ == "__main__":
    main()