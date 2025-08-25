import os
import asyncio
import logging
from io import BytesIO
from typing import Optional, Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)
from telegram.constants import ParseMode
from loguru import logger
from PIL import Image

# Импорт наших модулей
from openai_handler import get_openai_handler
from ocr_handler import get_ocr_handler
from translator import get_translation_handler

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        
        # Инициализация обработчиков
        self.openai_handler = get_openai_handler()
        self.ocr_handler = get_ocr_handler()
        self.translation_handler = get_translation_handler()
        
        # Настройки
        self.max_image_size = int(os.getenv('MAX_IMAGE_SIZE', '10485760'))  # 10MB
        self.supported_formats = os.getenv('SUPPORTED_IMAGE_FORMATS', 'jpg,jpeg,png,bmp,tiff,webp').split(',')
        
        # Хранилище пользовательских настроек
        self.user_settings = {}
        
        # Создание приложения
        self.application = Application.builder().token(self.bot_token).build()
        self._setup_handlers()
        
        logger.info("Telegram бот инициализирован")
    
    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CommandHandler("languages", self.languages_command))
        self.application.add_handler(CommandHandler("setlang", self.setlang_command))
        
        # Обработка изображений
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(MessageHandler(filters.Document.IMAGE, self.handle_document))
        
        # Обработка текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
        # Обработка callback кнопок
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Обработка ошибок
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "Пользователь"
        
        # Инициализация настроек пользователя
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {
                'target_language': 'английский',
                'use_openai': True,
                'preserve_structure': True
            }
        
        welcome_text = f"""🤖 **Добро пожаловать, {user_name}!**

Я бот для распознавания и перевода текста с изображений. Вот что я умею:

📸 **Отправьте мне изображение** с текстом (чек, документ, фото)
📝 **Отправьте текст** для перевода
🌍 **Переведу на любой язык** с сохранением структуры

**Команды:**
/help - Помощь и инструкции
/settings - Настройки бота
/languages - Список доступных языков
/setlang [язык] - Установить язык перевода

**Поддерживаемые форматы изображений:**
{', '.join(self.supported_formats).upper()}

**Максимальный размер файла:** {self.max_image_size // 1024 // 1024} МБ

Просто отправьте изображение или текст, и я начну работу! 🚀"""
        
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Пользователь {user_id} ({user_name}) запустил бота")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        help_text = """📖 **Инструкция по использованию**

**1. Распознавание текста с изображений:**
• Отправьте фото или документ с текстом
• Бот автоматически распознает и переведет текст
• Структура оригинала будет сохранена

**2. Перевод текста:**
• Просто отправьте текстовое сообщение
• Бот переведет его на выбранный язык

**3. Настройки:**
• `/settings` - открыть панель настроек
• `/setlang русский` - установить русский как целевой язык
• `/languages` - посмотреть все доступные языки

**4. Поддерживаемые языки:**
Русский, Английский, Немецкий, Французский, Испанский, Итальянский, Португальский, Китайский, Японский, Корейский, Арабский, Турецкий и многие другие.

**5. Советы:**
• Для лучшего качества используйте четкие изображения
• Избегайте слишком мелкого текста
• Проверьте освещение на фото

**Возникли проблемы?** Попробуйте:
• Переснять изображение с лучшим качеством
• Использовать другой формат файла
• Проверить размер файла (макс. {self.max_image_size // 1024 // 1024} МБ)"""
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /settings"""
        user_id = update.effective_user.id
        settings = self.user_settings.get(user_id, {})
        
        current_lang = settings.get('target_language', 'английский')
        use_openai = settings.get('use_openai', True)
        preserve_structure = settings.get('preserve_structure', True)
        
        # Создание клавиатуры настроек
        keyboard = [
            [InlineKeyboardButton(f"🌍 Язык: {current_lang}", callback_data="change_language")],
            [InlineKeyboardButton(f"🤖 AI: {'OpenAI' if use_openai else 'Google'}", callback_data="toggle_ai")],
            [InlineKeyboardButton(f"📋 Структура: {'Сохранять' if preserve_structure else 'Не сохранять'}", callback_data="toggle_structure")],
            [InlineKeyboardButton("🔄 Сбросить настройки", callback_data="reset_settings")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = f"""⚙️ **Настройки бота**

**Текущие настройки:**
🌍 Целевой язык: **{current_lang}**
🤖 ИИ для перевода: **{'OpenAI GPT' if use_openai else 'Google Translate'}**
📋 Сохранение структуры: **{'Включено' if preserve_structure else 'Выключено'}**

Используйте кнопки ниже для изменения настроек:"""
        
        await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def languages_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /languages"""
        languages = await self.translation_handler.get_available_languages()
        
        # Группировка языков для удобного отображения
        lang_list = []
        for lang_name, lang_code in sorted(languages.items()):
            lang_list.append(f"• **{lang_name.capitalize()}** (`{lang_code}`)") 
        
        # Разбиваем на части, чтобы не превысить лимит сообщения
        chunk_size = 30
        chunks = [lang_list[i:i + chunk_size] for i in range(0, len(lang_list), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            header = "🌍 **Доступные языки для перевода:**\n\n" if i == 0 else ""
            text = header + "\n".join(chunk)
            
            if i == len(chunks) - 1:
                text += "\n\n**Использование:** `/setlang русский` или `/setlang ru`"
            
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def setlang_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /setlang"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "❌ Укажите язык!\n\nПример: `/setlang русский` или `/setlang ru`\n\nДля просмотра всех языков: /languages",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        target_language = " ".join(context.args).lower()
        
        # Проверка существования языка
        languages = await self.translation_handler.get_available_languages()
        lang_code = self.translation_handler.get_language_code(target_language)
        
        if lang_code not in languages.values() and target_language not in languages:
            await update.message.reply_text(
                f"❌ Язык '{target_language}' не найден!\n\nИспользуйте /languages для просмотра доступных языков.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Сохранение настройки
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        
        self.user_settings[user_id]['target_language'] = target_language
        
        lang_name = self.translation_handler.get_language_name(lang_code)
        await update.message.reply_text(
            f"✅ Язык перевода установлен: **{lang_name}** (`{lang_code}`)\n\nТеперь все переводы будут выполняться на этот язык.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Пользователь {user_id} установил язык: {target_language}")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка фотографий"""
        user_id = update.effective_user.id
        
        # Отправка сообщения о начале обработки
        processing_msg = await update.message.reply_text("🔄 Обрабатываю изображение...")
        
        try:
            # Получение файла
            photo = update.message.photo[-1]  # Берем самое большое разрешение
            file = await context.bot.get_file(photo.file_id)
            
            # Проверка размера
            if file.file_size > self.max_image_size:
                await processing_msg.edit_text(
                    f"❌ Файл слишком большой! Максимальный размер: {self.max_image_size // 1024 // 1024} МБ"
                )
                return
            
            # Скачивание изображения
            image_bytes = await self._download_file(file.file_path)
            if not image_bytes:
                await processing_msg.edit_text("❌ Не удалось скачать изображение")
                return
            
            # Обработка изображения
            await self._process_image(update, context, image_bytes, processing_msg, user_id)
            
        except Exception as e:
            logger.error(f"Ошибка обработки фото: {e}")
            await processing_msg.edit_text(f"❌ Ошибка обработки изображения: {str(e)}")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка документов (изображений)"""
        user_id = update.effective_user.id
        document = update.message.document
        
        # Проверка типа файла
        if not any(document.file_name.lower().endswith(f'.{fmt}') for fmt in self.supported_formats):
            await update.message.reply_text(
                f"❌ Неподдерживаемый формат файла!\n\nПоддерживаемые форматы: {', '.join(self.supported_formats).upper()}"
            )
            return
        
        # Проверка размера
        if document.file_size > self.max_image_size:
            await update.message.reply_text(
                f"❌ Файл слишком большой! Максимальный размер: {self.max_image_size // 1024 // 1024} МБ"
            )
            return
        
        processing_msg = await update.message.reply_text("🔄 Обрабатываю документ...")
        
        try:
            # Получение файла
            file = await context.bot.get_file(document.file_id)
            
            # Скачивание
            image_bytes = await self._download_file(file.file_path)
            if not image_bytes:
                await processing_msg.edit_text("❌ Не удалось скачать файл")
                return
            
            # Обработка
            await self._process_image(update, context, image_bytes, processing_msg, user_id)
            
        except Exception as e:
            logger.error(f"Ошибка обработки документа: {e}")
            await processing_msg.edit_text(f"❌ Ошибка обработки документа: {str(e)}")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        
        if not text or not text.strip():
            await update.message.reply_text("❌ Пустое сообщение")
            return
        
        # Получение настроек пользователя
        settings = self.user_settings.get(user_id, {})
        target_language = settings.get('target_language', 'русский')
        use_openai = settings.get('use_openai', True)
        
        processing_msg = await update.message.reply_text("🔄 Перевожу текст...")
        
        try:
            # Перевод текста
            result = await self.translation_handler.translate_text(
                text=text,
                target_lang=target_language,
                use_openai=use_openai
            )
            
            if result.get('success'):
                formatted_result = self.translation_handler.format_translation_result(result)
                await processing_msg.edit_text(formatted_result, parse_mode=ParseMode.MARKDOWN)
                
                logger.info(f"Пользователь {user_id} перевел текст (длина: {len(text)})")
            else:
                await processing_msg.edit_text(f"❌ Ошибка перевода: {result.get('error', 'Неизвестная ошибка')}")
                
        except Exception as e:
            logger.error(f"Ошибка перевода текста: {e}")
            await processing_msg.edit_text(f"❌ Ошибка перевода: {str(e)}")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на inline кнопки"""
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        await query.answer()
        
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        
        settings = self.user_settings[user_id]
        
        if data == "change_language":
            # Показать популярные языки
            keyboard = [
                [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_русский"),
                 InlineKeyboardButton("🇺🇸 English", callback_data="lang_английский")],
                [InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_немецкий"),
                 InlineKeyboardButton("🇫🇷 Français", callback_data="lang_французский")],
                [InlineKeyboardButton("🇪🇸 Español", callback_data="lang_испанский"),
                 InlineKeyboardButton("🇮🇹 Italiano", callback_data="lang_итальянский")],
                [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_китайский"),
                 InlineKeyboardButton("🇯🇵 日本語", callback_data="lang_японский")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_settings")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "🌍 **Выберите язык для перевода:**\n\nДля просмотра всех языков используйте /languages",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data.startswith("lang_"):
            language = data[5:]
            settings['target_language'] = language
            
            await query.edit_message_text(
                f"✅ Язык перевода изменен на: **{language.capitalize()}**\n\nИспользуйте /settings для других настроек.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "toggle_ai":
            settings['use_openai'] = not settings.get('use_openai', True)
            await self._update_settings_message(query, settings)
        
        elif data == "toggle_structure":
            settings['preserve_structure'] = not settings.get('preserve_structure', True)
            await self._update_settings_message(query, settings)
        
        elif data == "reset_settings":
            self.user_settings[user_id] = {
                'target_language': 'русский',
                'use_openai': True,
                'preserve_structure': True
            }
            await query.edit_message_text(
                "✅ Настройки сброшены к значениям по умолчанию!\n\nИспользуйте /settings для изменения настроек."
            )
        
        elif data == "back_to_settings":
            await self._update_settings_message(query, settings)
    
    async def _update_settings_message(self, query, settings):
        """Обновление сообщения с настройками"""
        current_lang = settings.get('target_language', 'английский')
        use_openai = settings.get('use_openai', True)
        preserve_structure = settings.get('preserve_structure', True)
        
        keyboard = [
            [InlineKeyboardButton(f"🌍 Язык: {current_lang}", callback_data="change_language")],
            [InlineKeyboardButton(f"🤖 AI: {'OpenAI' if use_openai else 'Google'}", callback_data="toggle_ai")],
            [InlineKeyboardButton(f"📋 Структура: {'Сохранять' if preserve_structure else 'Не сохранять'}", callback_data="toggle_structure")],
            [InlineKeyboardButton("🔄 Сбросить настройки", callback_data="reset_settings")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = f"""⚙️ **Настройки бота**

**Текущие настройки:**
🌍 Целевой язык: **{current_lang}**
🤖 ИИ для перевода: **{'OpenAI GPT' if use_openai else 'Google Translate'}**
📋 Сохранение структуры: **{'Включено' if preserve_structure else 'Выключено'}**

Используйте кнопки ниже для изменения настроек:"""
        
        await query.edit_message_text(settings_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def _download_file(self, file_path: str) -> Optional[bytes]:
        """Скачивание файла из Telegram"""
        try:
            url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"Ошибка скачивания файла: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Ошибка скачивания файла: {e}")
            return None
    
    async def _process_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           image_bytes: bytes, processing_msg, user_id: int):
        """Обработка изображения: OCR + перевод"""
        try:
            # Обновление статуса
            await processing_msg.edit_text("🔍 Распознаю текст на изображении...")
            
            # OCR
            ocr_result = await self.ocr_handler.extract_text_from_image(image_bytes)
            
            if not ocr_result.get('success'):
                await processing_msg.edit_text(f"❌ Ошибка распознавания: {ocr_result.get('error', 'Неизвестная ошибка')}")
                return
            
            extracted_text = ocr_result.get('text', '').strip()
            
            if not extracted_text:
                await processing_msg.edit_text("❌ Текст на изображении не найден")
                return
            
            # Получение настроек пользователя
            settings = self.user_settings.get(user_id, {})
            target_language = settings.get('target_language', 'английский')
            use_openai = settings.get('use_openai', True)
            preserve_structure = settings.get('preserve_structure', True)
            
            # Обновление статуса
            await processing_msg.edit_text(f"📝 Найден текст! Перевожу на {target_language}...")
            
            # Улучшение текста с помощью OpenAI (если включено)
            if use_openai and preserve_structure:
                try:
                    improved_text = await self.openai_handler.improve_ocr_text(extracted_text)
                    if improved_text:
                        extracted_text = improved_text
                        logger.info("Текст улучшен с помощью OpenAI")
                except Exception as e:
                    logger.warning(f"Не удалось улучшить текст: {e}")
            
            # Перевод
            translation_result = await self.translation_handler.translate_text(
                text=extracted_text,
                target_lang=target_language,
                use_openai=use_openai
            )
            
            if translation_result.get('success'):
                # Форматирование результата
                response_text = "📸 **Результат обработки изображения:**\n\n"
                
                # Добавляем информацию о распознанном тексте
                response_text += f"**🔍 Распознанный текст:**\n{extracted_text[:500]}{'...' if len(extracted_text) > 500 else ''}\n\n"
                
                # Добавляем перевод
                translated_text = translation_result['translated_text']
                source_lang = translation_result.get('source_language', 'неизвестный')
                target_lang = translation_result.get('target_language', target_language)
                service = translation_result.get('service', 'неизвестный сервис')
                
                response_text += f"**🔄 Перевод ({source_lang} → {target_lang}):**\n{translated_text}\n\n"
                response_text += f"_Переведено с помощью {service}_"
                
                # Отправка результата
                if len(response_text) > 4096:  # Лимит Telegram
                    # Разбиваем на части
                    parts = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
                    
                    await processing_msg.edit_text(parts[0], parse_mode=ParseMode.MARKDOWN)
                    
                    for part in parts[1:]:
                        await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
                else:
                    await processing_msg.edit_text(response_text, parse_mode=ParseMode.MARKDOWN)
                
                logger.info(f"Пользователь {user_id} успешно обработал изображение")
                
            else:
                error_msg = f"❌ Ошибка перевода: {translation_result.get('error', 'Неизвестная ошибка')}\n\n"
                error_msg += f"**Распознанный текст:**\n{extracted_text}"
                
                await processing_msg.edit_text(error_msg, parse_mode=ParseMode.MARKDOWN)
                
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {e}")
            await processing_msg.edit_text(f"❌ Ошибка обработки: {str(e)}")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок"""
        logger.error(f"Ошибка в боте: {context.error}")
        
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Произошла ошибка при обработке запроса. Попробуйте еще раз."
                )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
    
    async def start_polling(self):
        """Запуск бота в режиме polling"""
        logger.info("Запуск бота в режиме polling...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Бот запущен и готов к работе!")
        
        # Ожидание завершения
        try:
            await self.application.updater.idle()
        except KeyboardInterrupt:
            logger.info("Получен сигнал завершения")
        finally:
            await self.application.stop()
            logger.info("Бот остановлен")
    
    async def start_webhook(self, webhook_url: str, port: int = 8000):
        """Запуск бота в режиме webhook для Render"""
        logger.info(f"Настройка webhook: {webhook_url}")
        
        await self.application.initialize()
        await self.application.start()
        
        # Установка webhook
        await self.application.bot.set_webhook(url=webhook_url)
        
        # Запуск webhook сервера
        await self.application.updater.start_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="webhook",
            webhook_url=webhook_url
        )
        
        logger.info(f"Webhook сервер запущен на порту {port}")
        
        # Ожидание
        try:
            await self.application.updater.idle()
        except KeyboardInterrupt:
            logger.info("Получен сигнал завершения")
        finally:
            await self.application.stop()
            logger.info("Webhook сервер остановлен")

# Функция для создания и запуска бота
async def main():
    """Главная функция"""
    try:
        bot = TelegramBot()
        
        # Проверяем, нужен ли webhook режим
        webhook_url = os.getenv('WEBHOOK_URL')
        port = int(os.getenv('PORT', '8000'))
        
        if webhook_url:
            await bot.start_webhook(webhook_url, port)
        else:
            await bot.start_polling()
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Запуск бота
    asyncio.run(main())