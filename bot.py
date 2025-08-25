#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простейший HTTP сервер для тестирования деплоя на Render
Без зависимостей от telegram - только встроенные модули Python
"""

import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs

# Логирование
try:
    from loguru import logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class SimpleHandler(BaseHTTPRequestHandler):
    """Простой HTTP обработчик"""
    
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>UMBB Bot Server</title>
                <meta charset="utf-8">
            </head>
            <body>
                <h1>🤖 UMBB Bot Server</h1>
                <p>✅ Сервер работает!</p>
                <p>🐍 Python версия: {}</p>
                <p>📁 Рабочая директория: {}</p>
                <p>🔧 Переменные окружения:</p>
                <ul>
                    <li>PORT: {}</li>
                    <li>RENDER: {}</li>
                </ul>
                <hr>
                <h2>Доступные эндпоинты:</h2>
                <ul>
                    <li><a href="/health">/health</a> - проверка здоровья</li>
                    <li><a href="/webhook">/webhook</a> - webhook для Telegram</li>
                </ul>
            </body>
            </html>
            """.format(
                sys.version,
                os.getcwd(),
                os.environ.get('PORT', 'не установлен'),
                os.environ.get('RENDER', 'не установлен')
            )
            
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            health_data = {
                'status': 'ok',
                'message': 'Server is running',
                'python_version': sys.version,
                'working_directory': os.getcwd()
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
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                logger.info(f"Получен webhook: {data}")
                
                # Простой ответ
                response = {
                    'status': 'received',
                    'message': 'Webhook получен, но telegram модуль недоступен'
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                logger.error(f"Ошибка обработки webhook: {e}")
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {'error': str(e)}
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Переопределяем логирование"""
        logger.info(f"{self.address_string()} - {format % args}")

def main():
    """Главная функция"""
    # Получаем порт из переменных окружения
    port = int(os.environ.get('PORT', 8000))
    
    logger.info(f"🚀 Запуск сервера на порту {port}")
    logger.info(f"🐍 Python версия: {sys.version}")
    logger.info(f"📁 Рабочая директория: {os.getcwd()}")
    
    # Проверяем доступность telegram модуля
    try:
        import telegram
        logger.info(f"✅ telegram модуль доступен, версия: {telegram.__version__}")
    except ImportError as e:
        logger.warning(f"❌ telegram модуль недоступен: {e}")
        logger.info("🔄 Работаем в режиме простого HTTP сервера")
    
    # Создаем и запускаем сервер
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    
    try:
        logger.info(f"🌐 Сервер доступен по адресу: http://0.0.0.0:{port}")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("🛑 Остановка сервера...")
        server.shutdown()
    except Exception as e:
        logger.error(f"💥 Ошибка сервера: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()