#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тelegram бот для Render.com - ФИНАЛЬНАЯ ВЕРСИЯ
Использует только стандартную библиотеку Python
Полностью автономное решение без внешних зависимостей
"""

import os
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import sys
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'dummy_token')
PORT = int(os.getenv('PORT', 10000))
WEBHOOK_URL = os.getenv('WEBHOOK_URL', f'https://umbb-gpt-bot.onrender.com')

class TelegramAPI:
    """Простой клиент для Telegram Bot API"""
    
    def __init__(self, token):
        self.token = token
        self.base_url = f'https://api.telegram.org/bot{token}'
    
    def send_message(self, chat_id, text, parse_mode='HTML'):
        """Отправка сообщения"""
        if self.token == 'dummy_token':
            logger.warning(f"🤖 Dummy mode: would send to {chat_id}: {text[:50]}...")
            return {'ok': True, 'result': {'message_id': 1}}
        
        url = f'{self.base_url}/sendMessage'
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        try:
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=data_encoded, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                logger.info(f"✅ Сообщение отправлено в чат {chat_id}")
                return result
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")
            return {'ok': False, 'error': str(e)}
    
    def set_webhook(self, webhook_url):
        """Установка webhook"""
        if self.token == 'dummy_token':
            logger.warning(f"🤖 Dummy mode: would set webhook to {webhook_url}")
            return {'ok': True}
        
        url = f'{self.base_url}/setWebhook'
        data = {'url': webhook_url}
        
        try:
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=data_encoded, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except Exception as e:
            logger.error(f"❌ Ошибка установки webhook: {e}")
            return {'ok': False, 'error': str(e)}

class WebhookHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов для webhook"""
    
    def log_message(self, format, *args):
        """Переопределяем для уменьшения шума в логах"""
        logger.info(f"HTTP: {format % args}")
    
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>🤖 UMBB GPT Bot</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .status {{ padding: 15px; border-radius: 5px; margin: 15px 0; }}
                    .success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                    .warning {{ background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
                    .error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                    .info {{ background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }}
                    h1 {{ color: #333; text-align: center; }}
                    .timestamp {{ font-size: 0.9em; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🤖 UMBB GPT Bot Status</h1>
                    
                    <div class="status success">
                        <strong>✅ HTTP Сервер:</strong> Работает на порту {PORT}
                    </div>
                    
                    <div class="status {'success' if BOT_TOKEN != 'dummy_token' else 'error'}">
                        <strong>{'✅' if BOT_TOKEN != 'dummy_token' else '❌'} Telegram Token:</strong> 
                        {'Настроен' if BOT_TOKEN != 'dummy_token' else 'НЕ НАСТРОЕН'}
                        {'' if BOT_TOKEN != 'dummy_token' else '<br><small>Установите TELEGRAM_BOT_TOKEN в Render Dashboard</small>'}
                    </div>
                    
                    <div class="status info">
                        <strong>🔗 Webhook URL:</strong> {WEBHOOK_URL}/webhook
                    </div>
                    
                    <div class="status info">
                        <strong>📱 Использование:</strong><br>
                        • Отправьте /start боту для начала<br>
                        • Отправьте /help для получения помощи<br>
                        • Отправьте любое текстовое сообщение для ответа
                    </div>
                    
                    <div class="timestamp">
                        Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </div>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health_data = {
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'bot_token_configured': BOT_TOKEN != 'dummy_token',
                'webhook_url': f'{WEBHOOK_URL}/webhook',
                'port': PORT
            }
            
            self.wfile.write(json.dumps(health_data, ensure_ascii=False).encode('utf-8'))
            
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_POST(self):
        """Обработка POST запросов (webhook)"""
        if self.path == '/webhook':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                if content_length > 0:
                    update_data = json.loads(post_data.decode('utf-8'))
                    logger.info(f"📨 Получен webhook: {json.dumps(update_data, ensure_ascii=False)[:200]}...")
                    
                    # Обработка обновления в отдельном потоке
                    threading.Thread(
                        target=self.process_telegram_update,
                        args=(update_data,),
                        daemon=True
                    ).start()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"ok": true}')
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки webhook: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': False, 'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def process_telegram_update(self, update_data):
        """Обработка обновления от Telegram"""
        try:
            telegram_api = TelegramAPI(BOT_TOKEN)
            
            # Обработка сообщений
            if 'message' in update_data:
                message = update_data['message']
                chat_id = message['chat']['id']
                
                if 'text' in message:
                    text = message['text']
                    logger.info(f"📝 Получено сообщение от {chat_id}: {text}")
                    
                    # Обработка команд
                    if text == '/start':
                        response = (
                            "🤖 <b>Добро пожаловать в UMBB GPT Bot!</b>\n\n"
                            "Я готов помочь вам с различными задачами.\n\n"
                            "<b>Доступные команды:</b>\n"
                            "• /start - Начать работу\n"
                            "• /help - Получить помощь\n\n"
                            "Просто отправьте мне любое сообщение, и я отвечу!"
                        )
                    elif text == '/help':
                        response = (
                            "🆘 <b>Помощь по использованию бота</b>\n\n"
                            "<b>Команды:</b>\n"
                            "• /start - Приветствие и начало работы\n"
                            "• /help - Эта справка\n\n"
                            "<b>Возможности:</b>\n"
                            "• Отвечаю на текстовые сообщения\n"
                            "• Обрабатываю фотографии\n"
                            "• Работаю через webhook на Render\n\n"
                            "<b>Статус:</b> ✅ Онлайн и готов к работе!"
                        )
                    else:
                        # Обработка обычных сообщений
                        responses = [
                            f"🤖 Получил ваше сообщение: '{text}'",
                            f"📝 Вы написали: {text}\n\nСпасибо за сообщение!",
                            f"💬 Отвечаю на '{text}': Интересное сообщение!",
                            f"🎯 Сообщение '{text}' обработано успешно!",
                            f"✨ Ваш текст '{text}' принят к обработке!"
                        ]
                        import random
                        response = random.choice(responses)
                    
                    telegram_api.send_message(chat_id, response)
                
                elif 'photo' in message:
                    logger.info(f"📸 Получено фото от {chat_id}")
                    response = (
                        "📸 <b>Фотография получена!</b>\n\n"
                        "Спасибо за отправленное изображение. "
                        "В данный момент я могу только подтвердить получение фото.\n\n"
                        "🔄 <i>Функция анализа изображений будет добавлена в будущих версиях.</i>"
                    )
                    telegram_api.send_message(chat_id, response)
                
                else:
                    logger.info(f"❓ Неизвестный тип сообщения от {chat_id}")
                    response = (
                        "🤔 <b>Неизвестный тип сообщения</b>\n\n"
                        "Я пока умею обрабатывать только текстовые сообщения и фотографии.\n\n"
                        "Попробуйте отправить текст или используйте команды /start или /help"
                    )
                    telegram_api.send_message(chat_id, response)
            
            else:
                logger.info(f"❓ Неизвестный тип обновления: {list(update_data.keys())}")
        
        except Exception as e:
            logger.error(f"❌ Ошибка обработки обновления: {e}")

def setup_webhook():
    """Настройка webhook"""
    logger.info("🔧 Настройка webhook...")
    
    # Проверка токена
    if BOT_TOKEN == 'dummy_token':
        logger.critical(
            "\n" + "="*60 + "\n"
            "❌ КРИТИЧЕСКАЯ ОШИБКА: TELEGRAM_BOT_TOKEN не настроен!\n\n"
            "Для работы бота необходимо:\n"
            "1. Получить токен от @BotFather в Telegram\n"
            "2. Зайти в Render Dashboard\n"
            "3. Открыть настройки вашего сервиса\n"
            "4. Добавить переменную окружения:\n"
            "   Имя: TELEGRAM_BOT_TOKEN\n"
            "   Значение: ваш_токен_от_botfather\n"
            "5. Перезапустить сервис\n\n"
            "Подробные инструкции в файле RENDER_SETUP.md\n"
            + "="*60
        )
        return False
    
    telegram_api = TelegramAPI(BOT_TOKEN)
    webhook_url = f'{WEBHOOK_URL}/webhook'
    
    logger.info(f"🔗 Установка webhook: {webhook_url}")
    logger.info(f"🔑 Токен: {BOT_TOKEN[:10]}...{BOT_TOKEN[-4:] if len(BOT_TOKEN) > 14 else '****'}")
    
    result = telegram_api.set_webhook(webhook_url)
    
    if result.get('ok'):
        logger.info("✅ Webhook успешно установлен!")
        return True
    else:
        error_msg = result.get('error', 'Неизвестная ошибка')
        logger.error(f"❌ Ошибка установки webhook: {error_msg}")
        logger.error("💡 Возможные причины:")
        logger.error("   • Неверный токен бота")
        logger.error("   • Проблемы с сетью")
        logger.error("   • Недоступность Telegram API")
        return False

def run_server():
    """Запуск HTTP сервера"""
    server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
    logger.info(f"🚀 HTTP сервер запущен на порту {PORT}")
    
    # Настройка webhook в отдельном потоке
    webhook_thread = threading.Thread(target=setup_webhook, daemon=True)
    webhook_thread.start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
        server.shutdown()

def main():
    """Главная функция"""
    logger.info("🤖 Запуск UMBB GPT Bot (Финальная версия)")
    logger.info(f"📊 Конфигурация:")
    logger.info(f"   • Порт: {PORT}")
    logger.info(f"   • Webhook URL: {WEBHOOK_URL}")
    logger.info(f"   • Токен настроен: {'✅ Да' if BOT_TOKEN != 'dummy_token' else '❌ НЕТ'}")
    logger.info(f"   • Python версия: {sys.version}")
    
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()