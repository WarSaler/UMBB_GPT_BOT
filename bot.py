#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автономный Telegram Bot для Render
Использует только стандартную библиотеку Python
"""

import os
import json
import logging
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import time

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение переменных окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN') or 'dummy_token'
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://umbb-gpt-bot.onrender.com')

class TelegramAPI:
    """Простой клиент для Telegram Bot API"""
    
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(self, chat_id, text, reply_markup=None):
        """Отправка сообщения"""
        try:
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            
            if reply_markup:
                data['reply_markup'] = json.dumps(reply_markup)
            
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            
            req = urllib.request.Request(
                f"{self.base_url}/sendMessage",
                data=encoded_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('ok', False)
                
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            return False
    
    def set_webhook(self, webhook_url):
        """Установка webhook"""
        try:
            data = urllib.parse.urlencode({
                'url': f"{webhook_url}/webhook"
            }).encode('utf-8')
            
            req = urllib.request.Request(
                f"{self.base_url}/setWebhook",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('ok', False)
                
        except Exception as e:
            logger.error(f"Ошибка установки webhook: {e}")
            return False

class WebhookHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов"""
    
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            response = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>UMBB GPT Bot</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #2c3e50; text-align: center; }
                    .status { padding: 15px; margin: 20px 0; border-radius: 5px; }
                    .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                    .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
                    .code { background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🤖 UMBB GPT Bot</h1>
                    <div class="status success">
                        ✅ Бот успешно запущен и работает!
                    </div>
                    <div class="status info">
                        📡 Webhook активен и готов к приему сообщений
                    </div>
                    <div class="status info">
                        🔧 Используется автономная архитектура без внешних зависимостей
                    </div>
                    <p><strong>Как использовать:</strong></p>
                    <ol>
                        <li>Найдите бота в Telegram</li>
                        <li>Отправьте команду /start</li>
                        <li>Начните общение!</li>
                    </ol>
                    <div class="code">
                        Статус: Активен<br>
                        Порт: {port}<br>
                        Webhook: {webhook_url}/webhook
                    </div>
                </div>
            </body>
            </html>
            """.format(port=PORT, webhook_url=WEBHOOK_URL)
            
            self.wfile.write(response.encode('utf-8'))
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'healthy',
                'bot_token_set': bool(BOT_TOKEN and BOT_TOKEN != 'dummy_token'),
                'webhook_url': f"{WEBHOOK_URL}/webhook"
            }).encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Обработка POST запросов (webhook)"""
        if self.path == '/webhook':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Парсинг JSON данных от Telegram
                update_data = json.loads(post_data.decode('utf-8'))
                
                # Обработка обновления
                self.process_telegram_update(update_data)
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
                
            except Exception as e:
                logger.error(f"Ошибка обработки webhook: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def process_telegram_update(self, update_data):
        """Обработка обновления от Telegram"""
        try:
            if 'message' in update_data:
                message = update_data['message']
                chat_id = message['chat']['id']
                
                # Обработка команд
                if 'text' in message:
                    text = message['text']
                    
                    if text == '/start':
                        self.handle_start_command(chat_id)
                    elif text == '/help':
                        self.handle_help_command(chat_id)
                    else:
                        self.handle_text_message(chat_id, text)
                
                # Обработка фото
                elif 'photo' in message:
                    self.handle_photo_message(chat_id)
                    
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
    
    def handle_start_command(self, chat_id):
        """Обработка команды /start"""
        telegram_api = TelegramAPI(BOT_TOKEN)
        
        message = """
🤖 <b>Добро пожаловать в UMBB GPT Bot!</b>

✨ Я готов помочь вам с:
• 💬 Ответами на вопросы
• 🖼️ Анализом изображений
• 📝 Обработкой текста

<b>Доступные команды:</b>
/start - Начать работу
/help - Получить помощь

🚀 Просто отправьте мне сообщение или фото!
        """
        
        telegram_api.send_message(chat_id, message)
        logger.info(f"Отправлена команда /start для chat_id: {chat_id}")
    
    def handle_help_command(self, chat_id):
        """Обработка команды /help"""
        telegram_api = TelegramAPI(BOT_TOKEN)
        
        message = """
🆘 <b>Справка по использованию бота:</b>

<b>Основные функции:</b>
• 💬 Отправьте текстовое сообщение - получите ответ
• 🖼️ Отправьте фото - получите описание
• ❓ Задайте любой вопрос

<b>Команды:</b>
/start - Перезапустить бота
/help - Показать эту справку

<b>Примеры использования:</b>
• "Расскажи анекдот"
• "Что на этом фото?" (с прикрепленным изображением)
• "Помоги с задачей по математике"

🤖 Я работаю 24/7 и готов помочь!
        """
        
        telegram_api.send_message(chat_id, message)
        logger.info(f"Отправлена команда /help для chat_id: {chat_id}")
    
    def handle_text_message(self, chat_id, text):
        """Обработка текстового сообщения"""
        telegram_api = TelegramAPI(BOT_TOKEN)
        
        # Простые ответы на популярные вопросы
        responses = {
            'привет': '👋 Привет! Как дела?',
            'как дела': '😊 У меня все отлично! А у вас?',
            'что умеешь': '🤖 Я могу отвечать на вопросы, анализировать фото и помогать с задачами!',
            'спасибо': '🙏 Пожалуйста! Рад помочь!',
            'пока': '👋 До свидания! Обращайтесь еще!'
        }
        
        # Поиск подходящего ответа
        response = None
        text_lower = text.lower()
        
        for key, value in responses.items():
            if key in text_lower:
                response = value
                break
        
        # Если не найден готовый ответ, генерируем универсальный
        if not response:
            response = f"📝 Получил ваше сообщение: <i>{text}</i>\n\n🤖 Это базовая версия бота. Для расширенной функциональности (GPT, анализ изображений) требуется подключение дополнительных API.\n\n💡 Попробуйте команды /start или /help для получения дополнительной информации!"
        
        telegram_api.send_message(chat_id, response)
        logger.info(f"Отправлен ответ на текст для chat_id: {chat_id}")
    
    def handle_photo_message(self, chat_id):
        """Обработка фото сообщения"""
        telegram_api = TelegramAPI(BOT_TOKEN)
        
        message = """
📸 <b>Фото получено!</b>

🔍 В базовой версии бота я могу только подтвердить получение изображения.

🚀 <b>Для полного анализа фото потребуется:</b>
• Подключение к OpenAI Vision API
• Или другому сервису анализа изображений

💡 Попробуйте отправить текстовое сообщение или используйте команды /start, /help
        """
        
        telegram_api.send_message(chat_id, message)
        logger.info(f"Обработано фото для chat_id: {chat_id}")
    
    def log_message(self, format, *args):
        """Переопределение логирования для уменьшения шума"""
        if not any(x in format % args for x in ['GET /', 'POST /webhook']):
            super().log_message(format, *args)

def setup_webhook():
    """Установка webhook"""
    if BOT_TOKEN == 'dummy_token':
        logger.warning("⚠️ Используется dummy token, webhook не будет установлен")
        return False
    
    telegram_api = TelegramAPI(BOT_TOKEN)
    
    logger.info(f"🔗 Установка webhook: {WEBHOOK_URL}/webhook")
    
    if telegram_api.set_webhook(WEBHOOK_URL):
        logger.info("✅ Webhook успешно установлен")
        return True
    else:
        logger.error("❌ Ошибка установки webhook")
        return False

def run_server():
    """Запуск HTTP сервера"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
        logger.info(f"🚀 HTTP сервер запущен на порту {PORT}")
        logger.info(f"🌐 Доступен по адресу: {WEBHOOK_URL}")
        
        # Установка webhook в отдельном потоке
        webhook_thread = Thread(target=lambda: time.sleep(2) or setup_webhook())
        webhook_thread.daemon = True
        webhook_thread.start()
        
        server.serve_forever()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска сервера: {e}")
        raise

def main():
    """Главная функция"""
    logger.info("🤖 Запуск автономного Telegram бота...")
    logger.info(f"📊 Конфигурация:")
    logger.info(f"   • Порт: {PORT}")
    logger.info(f"   • Webhook URL: {WEBHOOK_URL}")
    logger.info(f"   • Bot Token: {'✅ Установлен' if BOT_TOKEN != 'dummy_token' else '⚠️ Dummy token'}")
    
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("🛑 Сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()