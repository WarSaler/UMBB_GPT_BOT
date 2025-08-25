#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальная рабочая версия Telegram Bot
"""

import os
import asyncio
import logging
from io import BytesIO
from typing import Optional, Dict, Any

# Импорт telegram модулей с обработкой ошибок
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler, CallbackQueryHandler,
        filters, ContextTypes
    )
    from telegram.constants import ParseMode
    print("✅ Успешный импорт telegram модулей")
except ImportError as e:
    print(f"❌ Ошибка импорта telegram: {e}")
    raise

# Импорт логирования
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.info = print
    logger.error = print
    logger.warning = print

# Импорт наших минимальных обработчиков
try:
    from openai_handler_minimal import get_openai_handler
except ImportError as e:
    print(f"⚠️ Не удалось импортировать openai_handler_minimal: {e}")
    def get_openai_handler():
        return None

try:
    from ocr_handler_minimal import get_ocr_handler
except ImportError as e:
    print(f"⚠️ Не удалось импортировать ocr_handler_minimal: {e}")
    def get_ocr_handler():
        return None

try:
    from translator_minimal import get_translation_handler
except ImportError as e:
    print(f"⚠️ Не удалось импортировать translator_minimal: {e}")
    def get_translation_handler():
        return None

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        
        print(f"🔑 Bot token найден: {self.bot_token[:10]}...")
        
        # Инициализация обработчиков с проверкой
        try:
            self.openai_handler = get_openai_handler()
            print(f"🤖 OpenAI handler: {'✅ Инициализирован' if self.openai_handler else '❌ Недоступен'}")
        except Exception as e:
            print(f"⚠️ Ошибка инициализации OpenAI handler: {e}")
            self.openai_handler = None
            
        try:
            self.ocr_handler = get_ocr_handler()
            print(f"👁️ OCR handler: {'✅ Инициализирован' if self.ocr_handler else '❌ Недоступен'}")
        except Exception as e:
            print(f"⚠️ Ошибка инициализации OCR handler: {e}")
            self.ocr_handler = None
            
        try:
            self.translation_handler = get_translation_handler()
            print(f"🌐 Translation handler: {'✅ Инициализирован' if self.translation_handler else '❌ Недоступен'}")
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
            print("✅ Telegram бот инициализирован успешно")
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
            self.application.add_handler(CommandHandler("status", self.status_command))
            
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
            user_name = update.effective_user.first_name or "Пользователь"
            
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
                f"🤖 Привет, {user_name}! Добро пожаловать в UMBB GPT Bot!\n\n"
                "Я могу помочь вам с:\n"
                "📸 Распознаванием текста с изображений (OCR)\n"
                "🌐 Переводом текста\n"
                "🤖 Улучшением качества распознанного текста\n\n"
                "📋 Доступные команды:\n"
                "/help - Справка\n"
                "/status - Статус сервисов\n"
                "/languages - Список языков\n\n"
                "📤 Просто отправьте мне:\n"
                "• Изображение с текстом для распознавания\n"
                "• Текст для перевода\n\n"
                "🚀 Давайте начнем!"
            )
            
            await update.message.reply_text(welcome_text)
            print(f"👤 Новый пользователь: {user_name} (ID: {user_id})")
            
        except Exception as e:
            print(f"❌ Ошибка в start_command: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке команды.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = (
            "📋 **Доступные команды:**\n\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать это сообщение\n"
            "/status - Проверить статус сервисов\n"
            "/languages - Список доступных языков\n"
            "/setlang <код> - Установить язык перевода\n\n"
            "📸 **Как использовать:**\n"
            "• Отправьте изображение с текстом для распознавания\n"
            "• Отправьте текст для перевода\n"
            "• Используйте команды для настройки\n\n"
            "🔧 **Поддерживаемые форматы изображений:**\n"
            "JPG, PNG, BMP, TIFF, WebP\n\n"
            "💡 **Совет:** Для лучшего качества OCR используйте четкие изображения с хорошим освещением."
        )
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status"""
        status_text = (
            "🔍 **Статус сервисов:**\n\n"
            f"🤖 OpenAI Handler: {'✅ Работает' if self.openai_handler else '❌ Недоступен'}\n"
            f"👁️ OCR Handler: {'✅ Работает' if self.ocr_handler else '❌ Недоступен'}\n"
            f"🌐 Translation Handler: {'✅ Работает' if self.translation_handler else '❌ Недоступен'}\n\n"
            f"📊 **Статистика:**\n"
            f"👥 Активных пользователей: {len(self.user_settings)}\n"
            f"💾 Максимальный размер изображения: {self.max_image_size // 1024 // 1024} MB\n"
            f"🖼️ Поддерживаемые форматы: {', '.join(self.supported_formats)}\n\n"
            "🚀 Бот работает нормально!"
        )
        
        await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
    
    async def languages_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /languages"""
        languages_text = (
            "🌐 **Поддерживаемые языки:**\n\n"
            "🇷🇺 `ru` - Русский\n"
            "🇺🇸 `en` - English\n"
            "🇩🇪 `de` - Deutsch\n"
            "🇫🇷 `fr` - Français\n"
            "🇪🇸 `es` - Español\n"
            "🇮🇹 `it` - Italiano\n"
            "🇵🇹 `pt` - Português\n"
            "🇨🇳 `zh` - 中文\n"
            "🇯🇵 `ja` - 日本語\n"
            "🇰🇷 `ko` - 한국어\n\n"
            "💡 Используйте `/setlang <код>` для установки языка перевода\n"
            "Например: `/setlang en` для английского"
        )
        
        await update.message.reply_text(languages_text, parse_mode=ParseMode.MARKDOWN)
    
    async def setlang_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /setlang"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "❌ Укажите код языка.\n"
                "Пример: `/setlang en`\n"
                "Используйте /languages для списка доступных языков.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        language_code = context.args[0].lower()
        supported_languages = {
            'ru': 'Русский', 'en': 'English', 'de': 'Deutsch',
            'fr': 'Français', 'es': 'Español', 'it': 'Italiano',
            'pt': 'Português', 'zh': '中文', 'ja': '日本語', 'ko': '한국어'
        }
        
        if language_code not in supported_languages:
            await update.message.reply_text(
                f"❌ Язык `{language_code}` не поддерживается.\n"
                "Используйте /languages для списка доступных языков.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Обновляем настройки пользователя
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        
        self.user_settings[user_id]['target_language'] = language_code
        
        await update.message.reply_text(
            f"✅ Язык перевода установлен: **{supported_languages[language_code]}** (`{language_code}`)",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /settings"""
        user_id = update.effective_user.id
        settings = self.user_settings.get(user_id, {})
        
        settings_text = (
            "⚙️ **Ваши настройки:**\n\n"
            f"🌐 Язык перевода: `{settings.get('target_language', 'en')}`\n"
            f"🔍 Язык OCR: `{settings.get('ocr_language', 'rus+eng')}`\n"
            f"🤖 OpenAI перевод: {'✅ Включен' if settings.get('use_openai_translation', True) else '❌ Выключен'}\n"
            f"📝 Улучшение OCR: {'✅ Включено' if settings.get('improve_ocr', True) else '❌ Выключено'}\n\n"
            "💡 Используйте команды для изменения настроек:\n"
            "• `/setlang <код>` - изменить язык перевода\n"
            "• `/languages` - список доступных языков"
        )
        
        await update.message.reply_text(settings_text, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик фотографий"""
        try:
            user_id = update.effective_user.id
            user_settings = self.user_settings.get(user_id, {})
            
            # Отправляем сообщение о начале обработки
            processing_message = await update.message.reply_text("📸 Обрабатываю изображение...")
            
            if not self.ocr_handler:
                await processing_message.edit_text("❌ OCR сервис временно недоступен")
                return
            
            # Получаем файл изображения
            photo = update.message.photo[-1]  # Берем изображение наибольшего размера
            file = await context.bot.get_file(photo.file_id)
            
            # Проверяем размер файла
            if file.file_size > self.max_image_size:
                await processing_message.edit_text(
                    f"❌ Изображение слишком большое ({file.file_size // 1024 // 1024} MB). "
                    f"Максимальный размер: {self.max_image_size // 1024 // 1024} MB"
                )
                return
            
            # Скачиваем изображение
            image_data = BytesIO()
            await file.download_to_memory(image_data)
            image_bytes = image_data.getvalue()
            
            await processing_message.edit_text("🔍 Распознаю текст...")
            
            # Извлекаем текст
            ocr_language = user_settings.get('ocr_language', 'rus+eng')
            extracted_text = await self.ocr_handler.extract_text_from_image(image_bytes, ocr_language)
            
            if not extracted_text or extracted_text.strip() == "":
                await processing_message.edit_text("❌ Не удалось распознать текст на изображении")
                return
            
            # Улучшаем текст, если включено
            final_text = extracted_text
            if user_settings.get('improve_ocr', True) and self.translation_handler:
                await processing_message.edit_text("✨ Улучшаю качество текста...")
                improvement_result = await self.translation_handler.improve_text(extracted_text)
                if improvement_result.get('success'):
                    final_text = improvement_result.get('improved_text', extracted_text)
            
            # Переводим, если нужно
            target_language = user_settings.get('target_language', 'en')
            if target_language != 'auto' and self.translation_handler:
                await processing_message.edit_text("🌐 Перевожу текст...")
                translation_result = await self.translation_handler.translate_text(
                    final_text, target_language, 'auto'
                )
                if translation_result.get('success'):
                    translated_text = translation_result.get('translated_text', final_text)
                    source_lang = translation_result.get('source_language', 'unknown')
                    
                    result_text = (
                        f"📸 **Результат OCR:**\n\n"
                        f"🔤 **Распознанный текст** ({source_lang}):\n{final_text}\n\n"
                        f"🌐 **Перевод** ({target_language}):\n{translated_text}"
                    )
                else:
                    result_text = f"📸 **Распознанный текст:**\n\n{final_text}"
            else:
                result_text = f"📸 **Распознанный текст:**\n\n{final_text}"
            
            await processing_message.edit_text(result_text, parse_mode=ParseMode.MARKDOWN)
            print(f"📸 OCR обработка завершена для пользователя {user_id}")
            
        except Exception as e:
            print(f"❌ Ошибка в handle_photo: {e}")
            try:
                await processing_message.edit_text("❌ Произошла ошибка при обработке изображения")
            except:
                await update.message.reply_text("❌ Произошла ошибка при обработке изображения")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик документов"""
        document = update.message.document
        
        if not self.ocr_handler or not self.ocr_handler.is_supported_format(document.file_name):
            await update.message.reply_text(
                f"❌ Формат файла `{document.file_name}` не поддерживается.\n"
                f"Поддерживаемые форматы: {', '.join(self.supported_formats)}",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Обрабатываем как изображение
        await self.handle_photo(update, context)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        try:
            user_id = update.effective_user.id
            user_settings = self.user_settings.get(user_id, {})
            text = update.message.text
            
            if len(text) > 4000:
                await update.message.reply_text("❌ Текст слишком длинный (максимум 4000 символов)")
                return
            
            processing_message = await update.message.reply_text("🌐 Обрабатываю текст...")
            
            if not self.translation_handler:
                await processing_message.edit_text("❌ Сервис перевода временно недоступен")
                return
            
            target_language = user_settings.get('target_language', 'en')
            
            # Переводим текст
            translation_result = await self.translation_handler.translate_text(
                text, target_language, 'auto'
            )
            
            if translation_result.get('success'):
                original = translation_result.get('original_text')
                translated = translation_result.get('translated_text')
                source_lang = translation_result.get('source_language', 'unknown')
                target_lang = translation_result.get('target_language')
                method = translation_result.get('method', 'unknown')
                
                if source_lang == target_lang:
                    result_text = f"ℹ️ Текст уже на языке `{target_lang}`.\n\n**Текст:**\n{original}"
                else:
                    result_text = (
                        f"🌐 **Перевод** ({source_lang} → {target_lang})\n"
                        f"🔧 Метод: {method}\n\n"
                        f"📝 **Оригинал:**\n{original}\n\n"
                        f"🌍 **Перевод:**\n{translated}"
                    )
            else:
                error = translation_result.get('error', 'Неизвестная ошибка')
                result_text = f"❌ Ошибка перевода: {error}\n\n**Исходный текст:**\n{text}"
            
            await processing_message.edit_text(result_text, parse_mode=ParseMode.MARKDOWN)
            print(f"🌐 Перевод завершен для пользователя {user_id}")
            
        except Exception as e:
            print(f"❌ Ошибка в handle_text: {e}")
            try:
                await processing_message.edit_text("❌ Произошла ошибка при обработке текста")
            except:
                await update.message.reply_text("❌ Произошла ошибка при обработке текста")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        await query.answer("🔧 Функция в разработке")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Exception while handling an update: {context.error}")
        print(f"❌ Ошибка: {context.error}")
        
        if update and hasattr(update, 'effective_message'):
            try:
                await update.effective_message.reply_text(
                    "❌ Произошла внутренняя ошибка. Попробуйте позже."
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
            
            print("✅ Бот успешно запущен и ожидает сообщения!")
            print("📱 Найдите бота в Telegram и отправьте /start")
            
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
            print(f"🌐 Webhook URL: {webhook_url}")
            
            await self.application.initialize()
            await self.application.start()
            
            # Настройка webhook
            await self.application.updater.start_webhook(
                listen="0.0.0.0",
                port=port,
                webhook_url=webhook_url
            )
            
            print(f"✅ Webhook настроен успешно!")
            print(f"📱 Бот готов к работе через webhook")
            
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
        print("🤖 UMBB GPT Bot - Финальная версия")
        print("=" * 50)
        print("🔍 Инициализация...")
        
        bot = TelegramBot()
        
        # Определяем режим запуска
        webhook_url = os.getenv('WEBHOOK_URL')
        port = int(os.getenv('PORT', 10000))
        
        if webhook_url:
            print(f"🌐 Режим: Webhook")
            await bot.start_webhook(webhook_url, port)
        else:
            print(f"🔄 Режим: Polling")
            await bot.start_polling()
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
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