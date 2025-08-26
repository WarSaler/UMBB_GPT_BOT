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
import base64

# Импорт OpenAI (опционально)
try:
    import openai
    OPENAI_AVAILABLE = True
    print(f"✅ OpenAI успешно импортирован. Версия: {openai.__version__}")
except ImportError as e:
    OPENAI_AVAILABLE = False
    print(f"❌ OpenAI не установлен: {e}")
    print("⚠️ Используются базовые ответы.")
except Exception as e:
    OPENAI_AVAILABLE = False
    print(f"❌ Ошибка импорта OpenAI: {e}")
    print("⚠️ Используются базовые ответы.")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'dummy_token')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
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

class OpenAIAPI:
    """Клиент для работы с OpenAI API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        if OPENAI_AVAILABLE and api_key:
            openai.api_key = api_key
    
    def is_available(self):
        """Проверка доступности OpenAI API"""
        return OPENAI_AVAILABLE and bool(self.api_key)
    
    def generate_text_response(self, user_message):
        """Генерация ответа на текстовое сообщение"""
        if not self.is_available():
            return self._get_fallback_response(user_message)
        
        try:
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты полезный ассистент UMBB GPT Bot. Отвечай на русском языке, будь дружелюбным и информативным."},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Ошибка OpenAI API: {e}")
            return self._get_fallback_response(user_message)
    
    def analyze_image(self, image_url, user_message="Опиши это изображение"):
        """Анализ изображения через OpenAI Vision API"""
        if not self.is_available():
            return "🔍 Анализ изображений недоступен. Проверьте настройки OpenAI API."
        
        try:
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Проанализируй это изображение и ответь на русском языке: {user_message}"},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображения: {e}")
            return f"❌ Не удалось проанализировать изображение: {str(e)}"
    
    def _get_fallback_response(self, user_message):
        """Базовые ответы без ИИ"""
        responses = {
            "погода": "🌤️ Для получения актуальной погоды рекомендую проверить местные метеосводки или погодные приложения.",
            "новости": "📰 Для получения свежих новостей рекомендую посетить надежные новостные источники.",
            "время": f"🕐 Текущее время сервера: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}",
            "привет": "👋 Привет! Как дела? Чем могу помочь?",
            "как дела": "😊 У меня все отлично! Готов помочь вам с любыми вопросами.",
            "спасибо": "🙏 Пожалуйста! Всегда рад помочь!"
        }
        
        user_lower = user_message.lower()
        for key, response in responses.items():
            if key in user_lower:
                return response
        
        return f"🤖 Получил ваше сообщение: '{user_message}'. \n\n💡 Для полноценной работы с ИИ необходимо настроить OpenAI API ключ."

class WebhookHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов для webhook"""
    
    def __init__(self, *args, **kwargs):
        self.bot_token = BOT_TOKEN
        self.port = PORT
        self.webhook_url = WEBHOOK_URL
        super().__init__(*args, **kwargs)
    
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
                        <strong>✅ HTTP Сервер:</strong> Работает на порту {self.port}
                    </div>
                    
                    <div class="status {'success' if self.bot_token != 'dummy_token' else 'error'}">
                        <strong>{'✅' if self.bot_token != 'dummy_token' else '❌'} Telegram Token:</strong> 
                        {'Настроен' if self.bot_token != 'dummy_token' else 'НЕ НАСТРОЕН'}
                        {'' if self.bot_token != 'dummy_token' else '<br><small>Установите TELEGRAM_BOT_TOKEN в Render Dashboard</small>'}
                    </div>
                    
                    <div class="status info">
                        <strong>🔗 Webhook URL:</strong> {self.webhook_url}/webhook
                    </div>
                    
                    <div class="status {'success' if OPENAI_AVAILABLE else 'warning'}">
                        <strong>🧠 OpenAI API:</strong> 
                        {'✅ Доступен' if OPENAI_AVAILABLE else '❌ Недоступен'}
                        {f' (ключ: {"✅ Настроен" if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10 else "❌ Не настроен"})' if OPENAI_AVAILABLE else ''}
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
                'status': 'healthy',
                'bot_token_set': self.bot_token != 'dummy_token',
                'webhook_url': f'{self.webhook_url}/webhook'
            }
            
            self.wfile.write(json.dumps(health_data, ensure_ascii=False).encode('utf-8'))
            
        elif self.path == '/diagnostics':
            # Диагностический endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            diagnostics_data = {
                'bot_status': 'running',
                'bot_token_set': BOT_TOKEN != 'dummy_token',
                'openai_available': OPENAI_AVAILABLE,
                'openai_key_set': bool(OPENAI_API_KEY and len(OPENAI_API_KEY) > 10),
                'webhook_url': f'{WEBHOOK_URL}/webhook',
                'port': PORT,
                'python_version': sys.version,
                'timestamp': datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(diagnostics_data, ensure_ascii=False, indent=2).encode('utf-8'))
            
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
            openai_api = OpenAIAPI(OPENAI_API_KEY)
            
            # Обработка сообщений
            if 'message' in update_data:
                message = update_data['message']
                chat_id = message['chat']['id']
                
                if 'text' in message:
                    text = message['text']
                    logger.info(f"📝 Получено сообщение от {chat_id}: {text}")
                    
                    # Обработка команд
                    if text == '/start':
                        ai_status = "🧠 ИИ активен" if openai_api.is_available() else "⚠️ ИИ недоступен (базовые ответы)"
                        response = (
                            "🤖 <b>Добро пожаловать в UMBB GPT Bot!</b>\n\n"
                            "Я готов помочь вам с различными задачами с использованием искусственного интеллекта.\n\n"
                            "<b>Доступные команды:</b>\n"
                            "• /start - Начать работу\n"
                            "• /help - Получить помощь\n\n"
                            "<b>Возможности:</b>\n"
                            "🧠 Умные ответы с помощью GPT\n"
                            "🔍 Анализ изображений\n"
                            "💬 Естественное общение\n\n"
                            f"<b>Статус ИИ:</b> {ai_status}"
                        )
                    elif text == '/help':
                        ai_status = "🧠 ИИ активен" if openai_api.is_available() else "⚠️ ИИ недоступен"
                        response = (
                            "🆘 <b>Помощь по использованию бота</b>\n\n"
                            "<b>Команды:</b>\n"
                            "• /start - Приветствие и начало работы\n"
                            "• /help - Эта справка\n\n"
                            "<b>Возможности:</b>\n"
                            "🧠 Генерация умных ответов с помощью GPT-3.5\n"
                            "🔍 Анализ и описание изображений\n"
                            "💬 Естественное общение на русском языке\n"
                            "🌐 Работа через webhook на Render\n\n"
                            f"<b>Статус ИИ:</b> {ai_status}\n"
                            "<b>Статус бота:</b> ✅ Онлайн и готов к работе!"
                        )
                    else:
                        # Генерация ответа с помощью ИИ
                        logger.info(f"🧠 Генерация ответа для: {text}")
                        response = openai_api.generate_text_response(text)
                    
                    telegram_api.send_message(chat_id, response)
                
                elif 'photo' in message:
                    logger.info(f"📸 Получено фото от {chat_id}")
                    
                    # Получаем самое большое фото
                    photo = message['photo'][-1]  # Последнее фото - самое большое
                    file_id = photo['file_id']
                    
                    # Получаем URL файла через Telegram API
                    try:
                        file_info = self.get_file_info(file_id)
                        if file_info and 'file_path' in file_info:
                            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info['file_path']}"
                            
                            # Анализируем изображение с помощью ИИ
                            caption = message.get('caption', 'Опиши это изображение подробно')
                            logger.info(f"🔍 Анализ изображения: {caption}")
                            
                            response = openai_api.analyze_image(file_url, caption)
                        else:
                            response = "❌ Не удалось получить изображение для анализа."
                    except Exception as e:
                        logger.error(f"❌ Ошибка получения файла: {e}")
                        response = "❌ Произошла ошибка при обработке изображения."
                    
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
    
    def get_file_info(self, file_id):
        """Получение информации о файле от Telegram API"""
        if BOT_TOKEN == 'dummy_token':
            logger.warning(f"🤖 Dummy mode: would get file info for {file_id}")
            return None
        
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/getFile'
        data = {'file_id': file_id}
        
        try:
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=data_encoded, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get('ok'):
                    return result.get('result')
                else:
                    logger.error(f"❌ Ошибка получения файла: {result}")
                    return None
        except Exception as e:
            logger.error(f"❌ Ошибка запроса файла: {e}")
            return None

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
    
    # Диагностика OpenAI API
    logger.info(f"🧠 OpenAI API статус: {'✅ Доступен' if OPENAI_AVAILABLE else '❌ Недоступен'}")
    if OPENAI_API_KEY:
        logger.info(f"🔑 OpenAI API ключ: {'✅ Настроен' if len(OPENAI_API_KEY) > 10 else '⚠️ Слишком короткий'}")
    else:
        logger.warning("🔑 OpenAI API ключ не настроен!")
    
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()