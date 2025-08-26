#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot для Render с webhook поддержкой
Использует python-telegram-bot и FastAPI
"""

import os
import asyncio
import logging
from typing import Optional

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Попытка импорта python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ python-dotenv загружен успешно")
except ImportError:
    logger.warning("python-dotenv не найден, используем системные переменные")

# Попытка импорта FastAPI
try:
    from fastapi import FastAPI, Request
    import uvicorn
    fastapi_available = True
    logger.info("✅ FastAPI и uvicorn успешно импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта FastAPI: {e}")
    fastapi_available = False
    FastAPI = None
    uvicorn = None

# Попытка импорта telegram
try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
    telegram_available = True
    logger.info("✅ Telegram модули успешно импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта telegram: {e}")
    telegram_available = False
    Update = None
    Bot = None
    Application = None
    CommandHandler = None
    MessageHandler = None
    filters = None
    CallbackQueryHandler = None

# Получение переменных окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://umbb-gpt-bot.onrender.com')

# Глобальные переменные
telegram_app: Optional[Application] = None
fastapi_app: Optional[FastAPI] = None

# Telegram bot функции (только если telegram доступен)
if telegram_available:
    async def start_command(update: Update, context) -> None:
        """Обработчик команды /start"""
        await update.message.reply_text(
            "🤖 Привет! Я UMBB GPT Bot.\n\n"
            "Отправь мне текст или фото, и я помогу тебе!\n\n"
            "Команды:\n"
            "/start - Начать работу\n"
            "/help - Помощь"
        )

    async def help_command(update: Update, context) -> None:
        """Обработчик команды /help"""
        await update.message.reply_text(
            "🆘 Помощь:\n\n"
            "• Отправь текст - получишь ответ от GPT\n"
            "• Отправь фото - получишь описание\n"
            "• /start - Начать заново\n"
            "• /help - Эта справка"
        )

    async def handle_message(update: Update, context) -> None:
        """Обработчик текстовых сообщений"""
        user_message = update.message.text
        logger.info(f"Получено сообщение: {user_message}")
        
        # Простой ответ (можно расширить с помощью OpenAI API)
        response = f"Получил ваше сообщение: {user_message}\n\nЭто базовый ответ. Для полной функциональности подключите OpenAI API."
        
        await update.message.reply_text(response)

    async def handle_photo(update: Update, context) -> None:
        """Обработчик фотографий"""
        logger.info("Получено фото")
        
        response = "📸 Фото получено!\n\nДля анализа изображений подключите OpenAI Vision API."
        
        await update.message.reply_text(response)

    async def button_callback(update: Update, context) -> None:
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(f"Выбрано: {query.data}")

def setup_telegram_bot() -> Optional[Application]:
    """Настройка Telegram бота"""
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        return None
    
    if not telegram_available:
        logger.error("❌ Telegram модули недоступны")
        return None
    
    try:
        # Создание приложения
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Добавление обработчиков
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        app.add_handler(CallbackQueryHandler(button_callback))
        
        logger.info("✅ Telegram бот настроен успешно")
        return app
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки Telegram бота: {e}")
        return None

def setup_fastapi() -> Optional[FastAPI]:
    """Настройка FastAPI приложения"""
    if not fastapi_available:
        logger.error("❌ FastAPI недоступен")
        return None
    
    try:
        app = FastAPI(title="UMBB GPT Bot", version="1.0.0")
        
        @app.get("/")
        async def root():
            return {
                "status": "ok",
                "message": "UMBB GPT Bot работает",
                "telegram_available": telegram_available,
                "fastapi_available": fastapi_available
            }
        
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        if telegram_available and telegram_app:
            @app.post("/webhook")
            async def webhook(request: Request):
                """Обработка webhook от Telegram"""
                try:
                    json_data = await request.json()
                    update = Update.de_json(json_data, telegram_app.bot)
                    await telegram_app.process_update(update)
                    return {"status": "ok"}
                except Exception as e:
                    logger.error(f"Ошибка обработки webhook: {e}")
                    return {"status": "error", "message": str(e)}
        
        logger.info("✅ FastAPI настроен успешно")
        return app
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки FastAPI: {e}")
        return None

async def setup_webhook():
    """Установка webhook для Telegram"""
    if not telegram_available or not telegram_app:
        logger.error("❌ Telegram недоступен для установки webhook")
        return False
    
    try:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await telegram_app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"]
        )
        logger.info(f"✅ Webhook установлен: {webhook_url}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")
        return False

def run_server():
    """Запуск сервера"""
    if not fastapi_available:
        logger.error("❌ FastAPI недоступен! Установите: pip install fastapi uvicorn")
        # Простой HTTP сервер как fallback
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class SimpleHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>UMBB GPT Bot</h1><p>FastAPI unavailable, using simple server</p>')
            
            def log_message(self, format, *args):
                logger.info(f"HTTP: {format % args}")
        
        logger.info(f"🚀 Запуск простого HTTP сервера на порту {PORT}")
        server = HTTPServer(('0.0.0.0', PORT), SimpleHandler)
        server.serve_forever()
        return
    
    try:
        logger.info(f"🚀 Запуск FastAPI сервера на порту {PORT}")
        uvicorn.run(
            fastapi_app,
            host="0.0.0.0",
            port=PORT,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"❌ Ошибка запуска сервера: {e}")

async def main():
    """Главная функция"""
    global telegram_app, fastapi_app
    
    logger.info("🤖 Запуск Telegram бота с webhook поддержкой...")
    
    # Настройка компонентов
    telegram_app = setup_telegram_bot()
    fastapi_app = setup_fastapi()
    
    if telegram_app:
        # Инициализация Telegram бота
        await telegram_app.initialize()
        await telegram_app.start()
        
        # Установка webhook
        await setup_webhook()
    
    # Запуск сервера
    run_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")