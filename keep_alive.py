#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keep Alive Script для предотвращения засыпания сервера на Render

Этот скрипт отправляет HTTP-запросы к серверу каждую минуту,
чтобы предотвратить его засыпание на бесплатном хостинге.
"""

import asyncio
import aiohttp
import time
from datetime import datetime
from typing import Optional
from loguru import logger
from config import get_config


class KeepAliveService:
    """
    Сервис для поддержания активности сервера
    """
    
    def __init__(self):
        self.config = get_config()
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_running = False
        self.ping_count = 0
        self.failed_pings = 0
        self.last_successful_ping = None
        self.start_time = datetime.now()
        
        # Настройки из конфигурации
        self.enabled = self.config.KEEP_ALIVE_ENABLED
        self.interval = self.config.KEEP_ALIVE_INTERVAL
        self.url = self.config.KEEP_ALIVE_URL
        self.timeout = 10  # Таймаут для запросов
        self.max_retries = 3  # Максимальное количество повторных попыток
        self.retry_delay = 5  # Задержка между повторными попытками
        
        logger.info(f"KeepAlive сервис инициализирован")
        logger.info(f"Enabled: {self.enabled}")
        logger.info(f"URL: {self.url}")
        logger.info(f"Interval: {self.interval} секунд")
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        await self.stop()
    
    async def start(self):
        """Запуск сервиса keep-alive"""
        if not self.enabled:
            logger.info("KeepAlive сервис отключен в конфигурации")
            return
        
        if self.is_running:
            logger.warning("KeepAlive сервис уже запущен")
            return
        
        # Создаем HTTP сессию
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'User-Agent': 'UMBB-GPT-Bot-KeepAlive/1.0',
                'Accept': 'application/json, text/plain, */*',
                'Connection': 'keep-alive'
            }
        )
        
        self.is_running = True
        self.start_time = datetime.now()
        
        logger.info("KeepAlive сервис запущен")
        
        # Запускаем основной цикл
        asyncio.create_task(self._keep_alive_loop())
    
    async def stop(self):
        """Остановка сервиса keep-alive"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.session:
            await self.session.close()
            self.session = None
        
        uptime = datetime.now() - self.start_time
        logger.info(f"KeepAlive сервис остановлен")
        logger.info(f"Время работы: {uptime}")
        logger.info(f"Всего пингов: {self.ping_count}")
        logger.info(f"Неудачных пингов: {self.failed_pings}")
    
    async def _keep_alive_loop(self):
        """Основной цикл keep-alive"""
        logger.info(f"Запуск цикла keep-alive с интервалом {self.interval} секунд")
        
        while self.is_running:
            try:
                # Выполняем пинг
                success = await self._ping_server()
                
                if success:
                    self.last_successful_ping = datetime.now()
                    if self.failed_pings > 0:
                        logger.info(f"Соединение восстановлено после {self.failed_pings} неудачных попыток")
                        self.failed_pings = 0
                else:
                    self.failed_pings += 1
                    logger.warning(f"Неудачный пинг #{self.failed_pings}")
                
                # Ждем до следующего пинга
                await asyncio.sleep(self.interval)
                
            except asyncio.CancelledError:
                logger.info("KeepAlive цикл был отменен")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле keep-alive: {e}")
                await asyncio.sleep(self.retry_delay)
    
    async def _ping_server(self) -> bool:
        """Отправка пинга на сервер"""
        if not self.session:
            logger.error("HTTP сессия не инициализирована")
            return False
        
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                self.ping_count += 1
                
                # Отправляем GET запрос на health endpoint
                async with self.session.get(self.url) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        logger.debug(
                            f"Пинг #{self.ping_count} успешен "
                            f"(статус: {response.status}, время: {response_time:.1f}мс)"
                        )
                        return True
                    else:
                        logger.warning(
                            f"Пинг #{self.ping_count} неудачен "
                            f"(статус: {response.status}, время: {response_time:.1f}мс)"
                        )
                        
                        # Если статус не 200, но сервер отвечает, считаем это частичным успехом
                        if response.status < 500:
                            return True
            
            except aiohttp.ClientError as e:
                logger.warning(f"Ошибка HTTP клиента при пинге #{self.ping_count} (попытка {attempt + 1}): {e}")
            except asyncio.TimeoutError:
                logger.warning(f"Таймаут при пинге #{self.ping_count} (попытка {attempt + 1})")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при пинге #{self.ping_count} (попытка {attempt + 1}): {e}")
            
            # Если это не последняя попытка, ждем перед повтором
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
        
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
    """Получение глобального экземпляра сервиса keep-alive"""
    global _keep_alive_service
    if _keep_alive_service is None:
        _keep_alive_service = KeepAliveService()
    return _keep_alive_service


async def start_keep_alive():
    """Запуск сервиса keep-alive"""
    service = get_keep_alive_service()
    await service.start()
    return service


async def stop_keep_alive():
    """Остановка сервиса keep-alive"""
    global _keep_alive_service
    if _keep_alive_service:
        await _keep_alive_service.stop()
        _keep_alive_service = None


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