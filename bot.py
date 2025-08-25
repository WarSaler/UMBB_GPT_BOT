#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot на основе python-telegram-bot 21.0.1
Полностью асинхронный бот с правильными импортами
"""

import os
import sys
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ python-dotenv загружен успешно")
except ImportError:
    logger.warning("python-dotenv не найден, используем системные переменные")

# Импорт Telegram модулей
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
    telegram_available = True
    logger.info("✅ Telegram модули успешно импортированы")
except ImportError as e:
    telegram_available = False
    logger.error(f"❌ Ошибка импорта telegram: {e}")
    logger.info("🔄 Работаем в режиме HTTP сервера")

# Получение переменных окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
PORT = int(os.getenv('PORT', 10000))

# HTTP сервер как fallback
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Telegram Bot Status</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>🤖 Telegram Bot Server</h1>
            <p>Сервер работает на порту {PORT}</p>
            <p>Статус: {'Telegram доступен' if telegram_available else 'HTTP режим'}</p>
            <p>Токен: {'Настроен' if BOT_TOKEN else 'Не найден'}</p>
        </body>
        </html>
        """
        
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        logger.info(f"HTTP: {format % args}")

# Telegram Bot функции
if telegram_available:
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        keyboard = [
            [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')],
            [InlineKeyboardButton("📊 Статус", callback_data='status')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👋 Привет, {update.effective_user.first_name}!\n\n"
            "🤖 Я многофункциональный Telegram бот.\n"
            "📝 Отправь мне текст или изображение для обработки.",
            reply_markup=reply_markup
        )

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        help_text = """
🆘 **Доступные команды:**

/start - Запустить бота
/help - Показать это сообщение

📝 **Возможности:**
• Обработка текстовых сообщений
• Анализ изображений
• Интерактивные кнопки

💡 Просто отправь мне сообщение или фото!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстовых сообщений"""
        user_text = update.message.text
        logger.info(f"Получено сообщение от {update.effective_user.username}: {user_text}")
        
        response = f"📨 Получил твоё сообщение: '{user_text}'\n\n"
        response += "🔄 Обрабатываю... (функция в разработке)"
        
        await update.message.reply_text(response)

    async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик изображений"""
        logger.info(f"Получено изображение от {update.effective_user.username}")
        
        await update.message.reply_text(
            "📸 Получил изображение!\n\n"
            "🔄 Анализ изображений в разработке..."
        )

    async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'help':
            await query.edit_message_text(
                "🆘 **Помощь**\n\n"
                "Этот бот может обрабатывать:\n"
                "• 📝 Текстовые сообщения\n"
                "• 📸 Изображения\n"
                "• 🔘 Интерактивные команды",
                parse_mode='Markdown'
            )
        elif query.data == 'status':
            await query.edit_message_text(
                "📊 **Статус бота**\n\n"
                "✅ Бот активен и работает\n"
                "🔗 Соединение установлено\n"
                "⚡ Готов к обработке запросов",
                parse_mode='Markdown'
            )

def run_http_server():
    """Запуск HTTP сервера"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), SimpleHandler)
        logger.info(f"🌐 HTTP сервер запущен на порту {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Ошибка HTTP сервера: {e}")

async def run_telegram_bot():
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
        
        # Запуск в режиме polling
        await app.run_polling(drop_pending_updates=True)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска Telegram бота: {e}")
        return False

def main():
    """Главная функция"""
    logger.info("🤖 Запуск бота...")
    
    # Проверяем доступность Telegram модулей и токена
    if telegram_available and BOT_TOKEN:
        logger.info("✅ Запуск в режиме Telegram бота")
        try:
            asyncio.run(run_telegram_bot())
        except Exception as e:
            logger.error(f"❌ Ошибка Telegram бота: {e}")
            logger.info("🔄 Переключение на HTTP сервер")
            run_http_server()
    else:
        if not telegram_available:
            logger.warning("⚠️ Telegram модули недоступны")
        if not BOT_TOKEN:
            logger.warning("⚠️ BOT_TOKEN не найден")
        logger.info("🌐 Запуск в режиме HTTP сервера")
        run_http_server()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        logger.info("🔄 Запуск аварийного HTTP сервера...")
        run_http_server()