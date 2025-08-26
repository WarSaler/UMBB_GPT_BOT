#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot для Render с полной поддержкой python-telegram-bot
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем пути для поиска модулей
sys.path.insert(0, '/opt/render/project/src')
sys.path.insert(0, '/app')
sys.path.insert(0, str(Path.cwd()))

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://umbb-gpt-bot.onrender.com')

# Проверка токена
if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == 'dummy_token':
    logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
    logger.error("📋 Инструкции:")
    logger.error("1. Получите токен от @BotFather в Telegram")
    logger.error("2. В Render Dashboard перейдите в Environment")
    logger.error("3. Добавьте переменную TELEGRAM_BOT_TOKEN с вашим токеном")
    logger.error("4. Перезапустите сервис")
    sys.exit(1)

try:
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from telegram.constants import ParseMode
    logger.info("✅ Telegram модули успешно импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта telegram: {e}")
    logger.error("💡 Попытка установки модулей...")
    
    import subprocess
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'python-telegram-bot[webhooks]==21.0.1'])
        logger.info("✅ Модули установлены, перезапуск...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as install_error:
        logger.error(f"❌ Не удалось установить модули: {install_error}")
        sys.exit(1)

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    import uvicorn
    logger.info("✅ FastAPI модули успешно импортированы")
except ImportError as e:
    logger.error(f"❌ Ошибка импорта FastAPI: {e}")
    logger.error("💡 Попытка установки FastAPI...")
    
    import subprocess
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'fastapi', 'uvicorn[standard]'])
        logger.info("✅ FastAPI установлен, перезапуск...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as install_error:
        logger.error(f"❌ Не удалось установить FastAPI: {install_error}")
        sys.exit(1)

# Создание приложения
app = FastAPI(title="UMBB GPT Bot")
bot_application = None

# Обработчики команд
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "🤖 <b>Добро пожаловать в UMBB GPT Bot!</b>\n\n"
        "Я готов помочь вам с различными задачами.\n\n"
        "📋 <b>Доступные команды:</b>\n"
        "/start - Показать это сообщение\n"
        "/help - Получить помощь\n\n"
        "💬 Просто напишите мне сообщение, и я отвечу!"
    )
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.HTML
    )
    logger.info(f"Пользователь {update.effective_user.id} запустил бота")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "🆘 <b>Помощь по использованию бота</b>\n\n"
        "🤖 Я - UMBB GPT Bot, готов помочь вам!\n\n"
        "📝 <b>Что я умею:</b>\n"
        "• Отвечать на ваши сообщения\n"
        "• Обрабатывать фотографии\n"
        "• Помогать с различными задачами\n\n"
        "💡 <b>Как использовать:</b>\n"
        "Просто напишите мне любое сообщение или отправьте фото!\n\n"
        "🔧 <b>Команды:</b>\n"
        "/start - Начать работу\n"
        "/help - Эта справка"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.HTML
    )
    logger.info(f"Пользователь {update.effective_user.id} запросил помощь")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Получено сообщение от {user_id}: {user_message}")
    
    # Простые ответы на популярные фразы
    responses = {
        "привет": "👋 Привет! Как дела?",
        "как дела": "😊 У меня всё отлично! А у вас?",
        "спасибо": "🙏 Пожалуйста! Рад помочь!",
        "пока": "👋 До свидания! Обращайтесь еще!",
        "помощь": "🆘 Используйте команду /help для получения справки"
    }
    
    response = responses.get(user_message.lower(), 
        f"📝 Вы написали: {user_message}\n\n🤖 Спасибо за сообщение! Я получил его и обработал.")
    
    await update.message.reply_text(response)
    logger.info(f"Отправлен ответ пользователю {user_id}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фотографий"""
    user_id = update.effective_user.id
    logger.info(f"Получена фотография от {user_id}")
    
    response = (
        "📸 <b>Фотография получена!</b>\n\n"
        "🔍 Я вижу, что вы отправили изображение.\n"
        "🤖 В будущих версиях я смогу анализировать фото!\n\n"
        "💡 Пока что просто подтверждаю получение."
    )
    
    await update.message.reply_text(
        response,
        parse_mode=ParseMode.HTML
    )
    logger.info(f"Отправлен ответ на фото пользователю {user_id}")

# FastAPI маршруты
@app.get("/")
async def root():
    return {
        "status": "running",
        "bot": "UMBB GPT Bot",
        "version": "2.0",
        "webhook_configured": bool(bot_application)
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": int(time.time())}

@app.post("/webhook")
async def webhook(request: Request):
    """Обработчик webhook от Telegram"""
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, bot_application.bot)
        await bot_application.process_update(update)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

async def setup_bot():
    """Настройка бота и webhook"""
    global bot_application
    
    try:
        # Создание приложения бота
        bot_application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Добавление обработчиков
        bot_application.add_handler(CommandHandler("start", start_command))
        bot_application.add_handler(CommandHandler("help", help_command))
        bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        bot_application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        # Инициализация бота
        await bot_application.initialize()
        await bot_application.start()
        
        # Настройка webhook
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await bot_application.bot.set_webhook(webhook_url)
        
        logger.info(f"✅ Бот успешно настроен")
        logger.info(f"🔗 Webhook URL: {webhook_url}")
        logger.info(f"🤖 Bot username: @{(await bot_application.bot.get_me()).username}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки бота: {e}")
        return False

def main():
    """Главная функция"""
    logger.info("🚀 Запуск UMBB GPT Bot v2.0")
    logger.info(f"🔧 Порт: {PORT}")
    logger.info(f"🌐 Webhook URL: {WEBHOOK_URL}")
    logger.info(f"🔑 Токен: {TELEGRAM_BOT_TOKEN[:10]}...")
    
    try:
        # Запуск сервера с настройкой бота
        import asyncio
        
        async def startup():
            await setup_bot()
        
        # Создание event loop для настройки бота
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(startup())
        
        # Запуск FastAPI сервера
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=PORT,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
    finally:
        if bot_application:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(bot_application.stop())
            loop.run_until_complete(bot_application.shutdown())
        logger.info("👋 Бот остановлен")

if __name__ == "__main__":
    main()