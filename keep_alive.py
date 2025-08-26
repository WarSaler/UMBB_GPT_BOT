#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keep Alive Script для предотвращения засыпания сервера на Render

Этот скрипт отправляет HTTP-запросы к серверу каждую минуту,
чтобы предотвратить его засыпание на бесплатном хостинге.
"""

import threading
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional
import os
from loguru import logger


class KeepAliveService:
    """
    Сервис для поддержания активности сервера
    """
    
    def __init__(self):
        self.thread: Optional[threading.Thread] = None
        self.is_running = False
        self.ping_count = 0
        self.failed_pings = 0
        self.last_successful_ping = None
        self.start_time = datetime.now()
        
        # Настройки из переменных окружения
        self.enabled = os.getenv('KEEP_ALIVE_ENABLED', 'true').lower() == 'true'
        self.interval = int(os.getenv('KEEP_ALIVE_INTERVAL', '60'))
        self.url = os.getenv('KEEP_ALIVE_URL') or os.getenv('WEBHOOK_URL') or 'http://localhost:10000'
        self.timeout = 10  # Таймаут для запросов
        self.max_retries = 3  # Максимальное количество повторных попыток
        self.retry_delay = 5  # Задержка между повторными попытками
        
        logger.info(f"KeepAlive сервис инициализирован")
        logger.info(f"Enabled: {self.enabled}")
        logger.info(f"URL: {self.url}")
        logger.info(f"Interval: {self.interval} секунд")
    
    def start(self):
        """Запуск сервиса keep-alive"""
        if not self.enabled:
            logger.info("KeepAlive сервис отключен в конфигурации")
            return
        
        if self.is_running:
            logger.warning("KeepAlive сервис уже запущен")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        
        logger.info("KeepAlive сервис запущен")
        
        # Запускаем основной цикл в отдельном потоке
        self.thread = threading.Thread(target=self._keep_alive_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Остановка сервиса keep-alive"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Ожидаем завершения потока
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        uptime = datetime.now() - self.start_time
        logger.info(f"KeepAlive сервис остановлен")
        logger.info(f"Время работы: {uptime}")
        logger.info(f"Всего пингов: {self.ping_count}")
        logger.info(f"Неудачных пингов: {self.failed_pings}")
    
    def _keep_alive_loop(self):
        """Основной цикл keep-alive"""
        logger.info(f"Запуск цикла keep-alive с интервалом {self.interval} секунд")
        
        while self.is_running:
            try:
                # Выполняем пинг
                success = self._ping_server()
                
                if success:
                    self.last_successful_ping = datetime.now()
                    if self.failed_pings > 0:
                        logger.info(f"Соединение восстановлено после {self.failed_pings} неудачных попыток")
                        self.failed_pings = 0
                else:
                    self.failed_pings += 1
                    logger.warning(f"Неудачный пинг #{self.failed_pings}")
                
                # Ждем до следующего пинга
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле keep-alive: {e}")
                time.sleep(self.retry_delay)
    
    def _ping_server(self) -> bool:
        """Отправка пинга на сервер"""
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                self.ping_count += 1
                
                # Создаем HTTP запрос
                request = urllib.request.Request(self.url)
                request.add_header('User-Agent', 'KeepAlive-Service/1.0')
                
                # Отправляем GET запрос
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    response_time = (time.time() - start_time) * 1000
                    status_code = response.getcode()
                    
                    if status_code == 200:
                        logger.debug(
                            f"Пинг #{self.ping_count} успешен "
                            f"(статус: {status_code}, время: {response_time:.1f}мс)"
                        )
                        return True
                    else:
                        logger.warning(
                            f"Пинг #{self.ping_count} неудачен "
                            f"(статус: {status_code}, время: {response_time:.1f}мс)"
                        )
                        
                        # Если статус не 200, но сервер отвечает, считаем это частичным успехом
                        if status_code < 500:
                            return True
            
            except urllib.error.HTTPError as e:
                logger.warning(f"HTTP ошибка при пинге #{self.ping_count} (попытка {attempt + 1}): {e.code} {e.reason}")
                # Если статус < 500, считаем частичным успехом
                if e.code < 500:
                    return True
            except urllib.error.URLError as e:
                logger.warning(f"URL ошибка при пинге #{self.ping_count} (попытка {attempt + 1}): {e}")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при пинге #{self.ping_count} (попытка {attempt + 1}): {e}")
            
            # Если это не последняя попытка, ждем перед повтором
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        return False
    
    def get_stats(self) -> dict:
        """Получение статистики работы сервиса"""
        uptime = datetime.now() - self.start_time if self.start_time else None
        
        return {
            'enabled': self.enabled,
            'running': self.is_running,
            'url': self.url,
            'interval': self.interval,
            'uptime': str(uptime) if uptime else None,
            'total_pings': self.ping_count,
            'failed_pings': self.failed_pings,
            'success_rate': (
                (self.ping_count - self.failed_pings) / self.ping_count * 100
                if self.ping_count > 0 else 0
            ),
            'last_successful_ping': (
                self.last_successful_ping.isoformat()
                if self.last_successful_ping else None
            )
        }
    
    async def manual_ping(self) -> dict:
        """Ручной пинг для тестирования"""
        if not self.session:
            await self.start()
        
        start_time = time.time()
        success = await self._ping_server()
        response_time = (time.time() - start_time) * 1000
        
        return {
            'success': success,
            'response_time_ms': round(response_time, 1),
            'url': self.url,
            'timestamp': datetime.now().isoformat()
        }


# Глобальный экземпляр сервиса
_keep_alive_service: Optional[KeepAliveService] = None


def get_keep_alive_service() -> KeepAliveService:
    """Получение экземпляра сервиса keep-alive (Singleton)"""
    global _keep_alive_service
    if _keep_alive_service is None:
        _keep_alive_service = KeepAliveService()
    return _keep_alive_service


def start_keep_alive():
    """Запуск сервиса keep-alive"""
    service = get_keep_alive_service()
    service.start()


def stop_keep_alive():
    """Остановка сервиса keep-alive"""
    service = get_keep_alive_service()
    service.stop()


if __name__ == "__main__":
    # Тестовый запуск сервиса
    async def main():
        logger.info("Запуск тестового режима KeepAlive сервиса")
        
        service = KeepAliveService()
        
        try:
            async with service:
                # Выполняем несколько тестовых пингов
                for i in range(5):
                    result = await service.manual_ping()
                    logger.info(f"Тестовый пинг {i+1}: {result}")
                    await asyncio.sleep(5)
                
                # Показываем статистику
                stats = service.get_stats()
                logger.info(f"Статистика: {stats}")
                
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания")
        except Exception as e:
            logger.error(f"Ошибка в тестовом режиме: {e}")
        
        logger.info("Тестовый режим завершен")
    
    # Запускаем тестовый режим
    asyncio.run(main())