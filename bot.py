#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой Telegram Bot для Render
Минимальные зависимости, максимальная совместимость
"""

import os
import json
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение переменных окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://umbb-gpt-bot.onrender.com')

# Проверка наличия токена
if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    BOT_TOKEN = "dummy_token"  # Заглушка для предотвращения краха

class TelegramWebhookHandler(BaseHTTPRequestHandler):
    """Обработчик webhook запросов от Telegram"""
    
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>UMBB GPT Bot</title>
                <meta charset="utf-8">
            </head>
            <body>
                <h1>🤖 UMBB GPT Bot</h1>
                <p>✅ Бот работает и готов к приему сообщений!</p>
                <p>🔗 Webhook URL: {WEBHOOK_URL}/webhook</p>
                <p>🚀 Статус: Активен</p>
                <p>⏰ Время: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </body>
            </html>
            """
            
            self.wfile.write(html_content.encode('utf-8'))
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health_data = {
                "status": "healthy",
                "bot_token_set": bool(BOT_TOKEN and BOT_TOKEN != "dummy_token"),
                "webhook_url": f"{WEBHOOK_URL}/webhook",
                "timestamp": time.time()
            }
            
            self.wfile.write(json.dumps(health_data).encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_POST(self):
        """Обработка POST запросов (webhook от Telegram)"""
        if self.path == '/webhook':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Парсим JSON данные от Telegram
                update_data = json.loads(post_data.decode('utf-8'))
                
                logger.info(f"📨 Получено обновление: {update_data}")
                
                # Обрабатываем обновление
                self.process_telegram_update(update_data)
                
                # Отправляем успешный ответ
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки webhook: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def process_telegram_update(self, update_data):
        """Обработка обновлений от Telegram"""
        try:
            if 'message' in update_data:
                message = update_data['message']
                chat_id = message['chat']['id']
                
                if 'text' in message:
                    text = message['text']
                    logger.info(f"💬 Сообщение от {chat_id}: {text}")
                    
                    # Обрабатываем команды
                    if text.startswith('/start'):
                        self.send_telegram_message(chat_id, "🤖 Привет! Я UMBB GPT Bot. Отправь мне сообщение!")
                    elif text.startswith('/help'):
                        help_text = (
                            "🆘 Помощь по боту:\n\n"
                            "/start - Запустить бота\n"
                            "/help - Показать эту справку\n\n"
                            "Просто отправь мне любое сообщение, и я отвечу!"
                        )
                        self.send_telegram_message(chat_id, help_text)
                    else:
                        # Простой ответ на обычные сообщения
                        response = f"📝 Получил твое сообщение: {text}\n\n🤖 Это простой ответ от UMBB GPT Bot!"
                        self.send_telegram_message(chat_id, response)
                        
                elif 'photo' in message:
                    logger.info(f"📸 Фото от {chat_id}")
                    self.send_telegram_message(chat_id, "📸 Получил твое фото! Пока что я не умею их обрабатывать, но скоро научусь!")
                    
            elif 'callback_query' in update_data:
                callback = update_data['callback_query']
                chat_id = callback['message']['chat']['id']
                data = callback['data']
                
                logger.info(f"🔘 Callback от {chat_id}: {data}")
                self.send_telegram_message(chat_id, f"✅ Нажата кнопка: {data}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка обработки обновления: {e}")
    
    def send_telegram_message(self, chat_id, text):
        """Отправка сообщения через Telegram Bot API"""
        try:
            import urllib.request
            import urllib.parse
            
            if BOT_TOKEN == "dummy_token":
                logger.warning("⚠️ Используется dummy токен, сообщение не отправлено")
                return
            
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=data_encoded, method='POST')
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get('ok'):
                    logger.info(f"✅ Сообщение отправлено в чат {chat_id}")
                else:
                    logger.error(f"❌ Ошибка отправки: {result}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
    
    def log_message(self, format, *args):
        """Переопределяем логирование для уменьшения шума"""
        pass

def setup_webhook():
    """Настройка webhook для Telegram"""
    try:
        import urllib.request
        import urllib.parse
        
        if BOT_TOKEN == "dummy_token":
            logger.warning("⚠️ Используется dummy токен, webhook не настроен")
            return False
        
        webhook_url = f"{WEBHOOK_URL}/webhook"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        
        data = {
            'url': webhook_url,
            'allowed_updates': json.dumps(["message", "callback_query"])
        }
        
        data_encoded = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_encoded, method='POST')
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('ok'):
                logger.info(f"✅ Webhook настроен: {webhook_url}")
                return True
            else:
                logger.error(f"❌ Ошибка настройки webhook: {result}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Ошибка настройки webhook: {e}")
        return False

def run_server():
    """Запуск HTTP сервера"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), TelegramWebhookHandler)
        logger.info(f"🚀 Сервер запущен на порту {PORT}")
        logger.info(f"🔗 Webhook URL: {WEBHOOK_URL}/webhook")
        
        # Настраиваем webhook в отдельном потоке
        webhook_thread = threading.Thread(target=setup_webhook)
        webhook_thread.daemon = True
        webhook_thread.start()
        
        # Запускаем сервер
        server.serve_forever()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска сервера: {e}")
        raise

def main():
    """Главная функция"""
    logger.info("🤖 Запуск UMBB GPT Bot...")
    logger.info(f"🔑 Токен установлен: {'✅' if BOT_TOKEN and BOT_TOKEN != 'dummy_token' else '❌'}")
    logger.info(f"🌐 Порт: {PORT}")
    logger.info(f"🔗 Webhook URL: {WEBHOOK_URL}")
    
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        exit(1)

if __name__ == "__main__":
    main()