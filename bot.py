#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot с поддержкой Webhooks для Render
Использует FastAPI для обработки webhook запросов
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

# Загрузка переменных окружения
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ python-dotenv загружен успешно")
except ImportError:
    logger.warning("python-dotenv не найден, используем системные переменные")

# Импорт необходимых модулей
try:
    import uvicorn
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import PlainTextResponse, HTMLResponse
    fastapi_available = True
    logger.info("✅ FastAPI модули успешно импортированы")
except ImportError as e:
    fastapi_available = False
    logger.error(f"❌ Ошибка импорта FastAPI: {e}")

# Импорт Telegram модулей
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
    telegram_available = True
    logger.info("✅ Telegram модули успешно импортированы")
except ImportError as e:
    telegram_available = False
    logger.error(f"❌ Ошибка импорта telegram: {e}")
    # Создаем заглушки для типов если импорт не удался
    Update = None
    InlineKeyboardButton = None
    InlineKeyboardMarkup = None
    Application = None
    CommandHandler = None
    MessageHandler = None
    CallbackQueryHandler = None
    ContextTypes = None
    filters = None

# Получение переменных окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL', f'https://umbb-gpt-bot.onrender.com')

# Глобальная переменная для приложения Telegram
if telegram_available and Application:
    telegram_app: Optional[Application] = None
else:
    telegram_app = None

# Создание FastAPI приложения
if fastapi_available:
    app = FastAPI(title="Telegram Bot Webhook")
else:
    app = None

# FastAPI endpoints (только если FastAPI доступен)
if fastapi_available and app:
    @app.get("/")
    async def root():
        """Главная страница для проверки статуса"""
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Telegram Bot Status</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>🤖 Telegram Bot Server</h1>
            <p>Сервер работает на порту {PORT}</p>
            <p>Статус Telegram: {'✅ Доступен' if telegram_available else '❌ Недоступен'}</p>
            <p>Статус FastAPI: {'✅ Доступен' if fastapi_available else '❌ Недоступен'}</p>
            <p>Токен: {'✅ Настроен' if BOT_TOKEN else '❌ Не найден'}</p>
            <p>Webhook URL: {WEBHOOK_URL}</p>
        </body>
        </html>
        """)

    @app.get("/health")
    @app.get("/healthcheck")
    async def health_check():
        """Health check endpoint для Render"""
        return PlainTextResponse("OK - Bot is running")

    @app.post("/webhook")
    async def webhook(request: Request):
        """Обработка webhook запросов от Telegram"""
        if not telegram_available or not telegram_app:
            raise HTTPException(status_code=503, detail="Telegram bot not available")
        
        try:
            # Получаем JSON данные от Telegram
            json_data = await request.json()
            
            # Создаем Update объект
            update = Update.de_json(json_data, telegram_app.bot)
            
            # Добавляем update в очередь для обработки
            await telegram_app.update_queue.put(update)
            
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Telegram Bot функции
if telegram_available:
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        user = update.effective_user
        logger.info(f"Пользователь {user.username} запустил бота")
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("🆘 Помощь", callback_data='help')],
            [InlineKeyboardButton("📊 Статус", callback_data='status')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = f"""
🤖 **Привет, {user.first_name}!**

Я - твой Telegram бот с поддержкой:
• 📝 Обработки текста
• 📸 Анализа изображений  
• 🔗 Webhook интеграции

💡 Отправь мне сообщение или используй кнопки ниже!
        """
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
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

async def setup_telegram_bot():
    """Настройка Telegram бота с webhook"""
    global telegram_app
    
    if not BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
        return False
    
    if not telegram_available:
        logger.error("❌ Telegram модули недоступны!")
        return False
    
    try:
        # Создание приложения без updater (для webhook)
        telegram_app = Application.builder().token(BOT_TOKEN).updater(None).build()
        
        # Добавление обработчиков
        telegram_app.add_handler(CommandHandler("start", start_command))
        telegram_app.add_handler(CommandHandler("help", help_command))
        telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        telegram_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        telegram_app.add_handler(CallbackQueryHandler(button_callback))
        
        # Инициализация приложения
        await telegram_app.initialize()
        await telegram_app.start()
        
        # Установка webhook
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await telegram_app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"]
        )
        
        logger.info(f"✅ Telegram бот настроен с webhook: {webhook_url}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки Telegram бота: {e}")
        return False

async def run_server():
    """Запуск FastAPI сервера"""
    if not fastapi_available:
        logger.error("❌ FastAPI недоступен!")
        return
    
    # Настройка Telegram бота
    await setup_telegram_bot()
    
    # Запуск FastAPI сервера
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    logger.info(f"🚀 Запуск FastAPI сервера на порту {PORT}")
    await server.serve()

def main():
    """Главная функция"""
    logger.info("🤖 Запуск Telegram бота с webhook поддержкой...")
    
    if not fastapi_available:
        logger.error("❌ FastAPI недоступен! Установите: pip install fastapi uvicorn")
        # Запускаем простой HTTP сервер без FastAPI
        import http.server
        import socketserver
        
        class SimpleHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>Bot Server Running</h1><p>FastAPI not available, but server is running.</p>')
            
            def log_message(self, format, *args):
                logger.info(f"HTTP: {format % args}")
        
        with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
            logger.info(f"🚀 Запуск простого HTTP сервера на порту {PORT}")
            httpd.serve_forever()
        return
    
    try:
        # Запуск FastAPI сервера с Telegram webhook
        asyncio.run(run_server())
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        exit(1)