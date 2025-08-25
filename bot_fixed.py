#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправленная версия Telegram Bot с правильными импортами
"""

import os
import asyncio
import logging
from io import BytesIO
from typing import Optional, Dict, Any

# Попробуем различные способы импорта telegram модулей
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, CallbackQueryHandler,
        filters, ContextTypes
    )
    from telegram.constants import ParseMode
    print("✅ Успешный импорт telegram модулей (стандартный способ)")
except ImportError as e:
    print(f"❌ Стандартный импорт не удался: {e}")
    try:
        # Альтернативный способ импорта
        import telegram
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import (
            Application, CommandHandler, MessageHandler, CallbackQueryHandler,
            filters, ContextTypes
        )
        from telegram.constants import ParseMode
        print("✅ Успешный импорт telegram модулей (альтернативный способ)")
    except ImportError as e2:
        print(f"❌ Альтернативный импорт не удался: {e2}")
        # Попробуем импорт через python_telegram_bot
        try:
            import python_telegram_bot as telegram
            from python_telegram_bot import Update, InlineKeyboardButton, InlineKeyboardMarkup
            from python_telegram_bot.ext import (
                Application, CommandHandler, MessageHandler, CallbackQueryHandler,
                filters, ContextTypes
            )
            from python_telegram_bot.constants import ParseMode
            print("✅ Успешный импорт через python_telegram_bot")
        except ImportError as e3:
            print(f"❌ Импорт через python_telegram_bot не удался: {e3}")
            raise ImportError(f"Не удалось импортировать telegram модули: {e}, {e2}, {e3}")

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.info = print
    logger.error = print
    logger.warning = print

try:
    from PIL import Image
except ImportError:
    print("❌ PIL не найден, функции обработки изображений будут недоступны")
    Image = None

# Импорт наших модулей с обработкой ошибок
try:
    from openai_handler import get_openai_handler
except ImportError as e:
    print(f"❌ Не удалось импортировать openai_handler: {e}")
    def get_openai_handler():
        return None

try:
    from ocr_handler import get_ocr_handler
except ImportError as e:
    print(f"❌ Не удалось импортировать ocr_handler: {e}")
    def get_ocr_handler():
        return None

try:
    from translator import get_translation_handler
except ImportError as e:
    print(f"❌ Не удалось импортировать translator: {e}")
    def get_translation_handler():
        return None

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        
        # Инициализация обработчиков с проверкой
        try:
            self.openai_handler = get_openai_handler()
        except Exception as e:
            print(f"⚠️ Ошибка инициализации OpenAI handler: {e}")
            self.openai_handler = None
            
        try:
            self.ocr_handler = get_ocr_handler()
        except Exception as e:
            print(f"⚠️ Ошибка инициализации OCR handler: {e}")
            self.ocr_handler = None
            
        try:
            self.translation_handler = get_translation_handler()
        except Exception as e:
            print(f"⚠️ Ошибка инициализации Translation handler: {e}")
            self.translation_handler = None
        
        # Настройки
        self.max_image_size = int(os.getenv('MAX_IMAGE_SIZE', '10485760'))  # 10MB
        self.supported_formats = os.getenv('SUPPORTED_IMAGE_FORMATS', 'jpg,jpeg,png,bmp,tiff,webp').split(',')
        
        # Хранилище пользовательских настроек
        self.user_settings = {}
        
        # Создание приложения
        try:
            self.application = Application.builder().token(self.bot_token).build()
            self._setup_handlers()
            logger.info("Telegram бот инициализирован")
        except Exception as e:
            print(f"❌ Ошибка создания приложения: {e}")
            raise
    
    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        try:
            # Команды
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("settings", self.settings_command))
            self.application.add_handler(CommandHandler("languages", self.languages_command))
            self.application.add_handler(CommandHandler("setlang", self.setlang_command))
            
            # Обработчики сообщений
            self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
            self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
            
            # Обработчик callback запросов
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            
            # Обработчик ошибок
            self.application.add_error_handler(self.error_handler)
            
            print("✅ Обработчики настроены успешно")
        except Exception as e:
            print(f"❌ Ошибка настройки обработчиков: {e}")
            raise
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        try:
            user_id = update.effective_user.id
            
            # Инициализация настроек пользователя
            if user_id not in self.user_settings:
                self.user_settings[user_id] = {
                    'source_language': 'auto',
                    'target_language': 'en',
                    'ocr_language': 'rus+eng',
                    'use_openai_translation': True,
                    'improve_ocr': True
                }
            
            welcome_text = (
                "🤖 Добро пожаловать в UMBB GPT Bot!\n\n"
                "Я могу помочь вам с:\n"
                "📸 Распознаванием текста с изображений (OCR)\n"
                "🌐 Переводом текста\n"
                "🤖 Улучшением качества распознанного текста\n\n"
                "Используйте /help для получения списка команд."
            )
            
            await update.message.reply_text(welcome_text)
        except Exception as e:
            print(f"❌ Ошибка в start_command: {e}")
            await update.message.reply_text("Произошла ошибка при обработке команды.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = (
            "📋 **Доступные команды:**\n\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать это сообщение\n"
            "/settings - Настройки бота\n"
            "/languages - Список доступных языков\n"
            "/setlang <код> - Установить язык перевода\n\n"
            "📸 **Как использовать:**\n"
            "• Отправьте изображение с текстом для распознавания\n"
            "• Отправьте текст для перевода\n"
            "• Используйте настройки для изменения языков\n\n"
            "🔧 **Поддерживаемые форматы изображений:**\n"
            "JPG, PNG, BMP, TIFF, WebP"
        )
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /settings"""
        await update.message.reply_text("⚙️ Настройки временно недоступны")
    
    async def languages_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /languages"""
        languages_text = (
            "🌐 **Поддерживаемые языки:**\n\n"
            "🇷🇺 ru - Русский\n"
            "🇺🇸 en - English\n"
            "🇩🇪 de - Deutsch\n"
            "🇫🇷 fr - Français\n"
            "🇪🇸 es - Español\n"
            "🇮🇹 it - Italiano\n"
            "🇵🇹 pt - Português\n"
            "🇨🇳 zh - 中文\n"
            "🇯🇵 ja - 日本語\n"
            "🇰🇷 ko - 한국어\n"
        )
        
        await update.message.reply_text(languages_text, parse_mode=ParseMode.MARKDOWN)
    
    async def setlang_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /setlang"""
        await update.message.reply_text("🔧 Функция установки языка временно недоступна")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик фотографий"""
        await update.message.reply_text("📸 Обработка изображений временно недоступна")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик документов"""
        await update.message.reply_text("📄 Обработка документов временно недоступна")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        text = update.message.text
        await update.message.reply_text(f"📝 Получен текст: {text[:100]}...")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        await query.answer("Функция временно недоступна")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and hasattr(update, 'effective_message'):
            try:
                await update.effective_message.reply_text(
                    "❌ Произошла ошибка при обработке вашего запроса. Попробуйте позже."
                )
            except Exception:
                pass
    
    async def start_polling(self):
        """Запуск бота в режиме polling"""
        try:
            print("🚀 Запуск бота в режиме polling...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            print("✅ Бот успешно запущен!")
            
            # Ожидание остановки
            await self.application.updater.idle()
            
        except Exception as e:
            print(f"❌ Ошибка при запуске polling: {e}")
            raise
        finally:
            await self.application.stop()
    
    async def start_webhook(self, webhook_url: str, port: int = 10000):
        """Запуск бота в режиме webhook"""
        try:
            print(f"🚀 Запуск бота в режиме webhook на порту {port}...")
            await self.application.initialize()
            await self.application.start()
            
            # Настройка webhook
            await self.application.updater.start_webhook(
                listen="0.0.0.0",
                port=port,
                webhook_url=webhook_url
            )
            
            print(f"✅ Webhook настроен: {webhook_url}")
            
            # Ожидание остановки
            await self.application.updater.idle()
            
        except Exception as e:
            print(f"❌ Ошибка при запуске webhook: {e}")
            raise
        finally:
            await self.application.stop()

async def main():
    """Главная функция"""
    try:
        print("🔍 Инициализация Telegram Bot...")
        bot = TelegramBot()
        
        # Определяем режим запуска
        webhook_url = os.getenv('WEBHOOK_URL')
        port = int(os.getenv('PORT', 10000))
        
        if webhook_url:
            print(f"🌐 Запуск в режиме webhook: {webhook_url}")
            await bot.start_webhook(webhook_url, port)
        else:
            print("🔄 Запуск в режиме polling")
            await bot.start_polling()
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    print("🤖 UMBB GPT Bot - Исправленная версия")
    print("=" * 50)
    
    # Настройка логирования
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Запуск бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Фатальная ошибка: {e}")
        exit(1)