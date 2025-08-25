import os
from typing import Optional, List
from loguru import logger
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class Config:
    """Класс для управления конфигурацией приложения"""
    
    def __init__(self):
        self._validate_required_env_vars()
        self._setup_logging()
        logger.info("Конфигурация загружена успешно")
    
    # === TELEGRAM BOT SETTINGS ===
    @property
    def telegram_bot_token(self) -> str:
        """Токен Telegram бота"""
        return os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    # === OPENAI SETTINGS ===
    @property
    def openai_api_key(self) -> str:
        """API ключ OpenAI"""
        return os.getenv('OPENAI_API_KEY', '')
    
    @property
    def openai_model(self) -> str:
        """Модель OpenAI для использования"""
        return os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    @property
    def openai_max_tokens(self) -> int:
        """Максимальное количество токенов для OpenAI"""
        return int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
    
    @property
    def openai_temperature(self) -> float:
        """Температура для OpenAI модели"""
        return float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
    
    # === SERVER SETTINGS ===
    @property
    def server_host(self) -> str:
        """Хост сервера"""
        return os.getenv('SERVER_HOST', '0.0.0.0')
    
    @property
    def server_port(self) -> int:
        """Порт сервера"""
        return int(os.getenv('PORT', '8000'))
    
    @property
    def webhook_url(self) -> Optional[str]:
        """URL для webhook (для Render)"""
        return os.getenv('WEBHOOK_URL')
    
    @property
    def app_url(self) -> Optional[str]:
        """URL приложения на Render"""
        return os.getenv('RENDER_EXTERNAL_URL')
    
    # === KEEP ALIVE SETTINGS ===
    @property
    def keep_alive_enabled(self) -> bool:
        """Включен ли keep-alive"""
        return os.getenv('KEEP_ALIVE_ENABLED', 'true').lower() == 'true'
    
    @property
    def keep_alive_interval(self) -> int:
        """Интервал keep-alive в секундах"""
        return int(os.getenv('KEEP_ALIVE_INTERVAL', '60'))
    
    @property
    def keep_alive_url(self) -> Optional[str]:
        """URL для keep-alive пингов"""
        return os.getenv('KEEP_ALIVE_URL') or self.app_url
    
    # === OCR SETTINGS ===
    @property
    def tesseract_cmd(self) -> Optional[str]:
        """Путь к команде tesseract"""
        return os.getenv('TESSERACT_CMD')
    
    @property
    def ocr_languages(self) -> List[str]:
        """Языки для OCR"""
        langs = os.getenv('OCR_LANGUAGES', 'eng,rus,deu,fra,spa,ita,por,chi_sim,jpn,kor')
        return [lang.strip() for lang in langs.split(',')]
    
    @property
    def ocr_engine(self) -> str:
        """Движок OCR по умолчанию"""
        return os.getenv('OCR_ENGINE', 'easyocr')
    
    # === LANGUAGE SETTINGS ===
    @property
    def default_source_language(self) -> str:
        """Исходный язык по умолчанию"""
        return os.getenv('DEFAULT_SOURCE_LANG', 'auto')
    
    @property
    def default_target_language(self) -> str:
        """Целевой язык по умолчанию"""
        return os.getenv('DEFAULT_TARGET_LANG', 'en')
    
    # === TRANSLATION SETTINGS ===
    @property
    def translation_service(self) -> str:
        """Сервис перевода по умолчанию"""
        return os.getenv('TRANSLATION_SERVICE', 'google')
    
    @property
    def google_translate_timeout(self) -> int:
        """Таймаут для Google Translate"""
        return int(os.getenv('GOOGLE_TRANSLATE_TIMEOUT', '10'))
    
    # === IMAGE PROCESSING SETTINGS ===
    @property
    def max_image_size(self) -> int:
        """Максимальный размер изображения в байтах"""
        return int(os.getenv('MAX_IMAGE_SIZE', '10485760'))  # 10MB
    
    @property
    def supported_image_formats(self) -> List[str]:
        """Поддерживаемые форматы изображений"""
        formats = os.getenv('SUPPORTED_IMAGE_FORMATS', 'jpg,jpeg,png,bmp,tiff,webp')
        return [fmt.strip().lower() for fmt in formats.split(',')]
    
    @property
    def image_preprocessing_enabled(self) -> bool:
        """Включена ли предобработка изображений"""
        return os.getenv('IMAGE_PREPROCESSING_ENABLED', 'true').lower() == 'true'
    
    # === LOGGING SETTINGS ===
    @property
    def log_level(self) -> str:
        """Уровень логирования"""
        return os.getenv('LOG_LEVEL', 'INFO')
    
    @property
    def log_format(self) -> str:
        """Формат логов"""
        return os.getenv('LOG_FORMAT', '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}')
    
    @property
    def log_file_enabled(self) -> bool:
        """Включено ли логирование в файл"""
        return os.getenv('LOG_FILE_ENABLED', 'false').lower() == 'true'
    
    @property
    def log_file_path(self) -> str:
        """Путь к файлу логов"""
        return os.getenv('LOG_FILE_PATH', 'logs/bot.log')
    

    
    # === CACHE SETTINGS ===
    @property
    def cache_enabled(self) -> bool:
        """Включено ли кэширование"""
        return os.getenv('CACHE_ENABLED', 'false').lower() == 'true'
    
    @property
    def cache_ttl_seconds(self) -> int:
        """Время жизни кэша в секундах"""
        return int(os.getenv('CACHE_TTL_SECONDS', '3600'))  # 1 час
    
    # === DEVELOPMENT SETTINGS ===
    @property
    def debug_mode(self) -> bool:
        """Режим отладки"""
        return os.getenv('DEBUG', 'false').lower() == 'true'
    
    @property
    def development_mode(self) -> bool:
        """Режим разработки"""
        return os.getenv('DEVELOPMENT', 'false').lower() == 'true'
    
    # === WEBHOOK SETTINGS ===
    @property
    def webhook_path(self) -> str:
        """Путь для webhook"""
        return os.getenv('WEBHOOK_PATH', '/webhook')
    
    @property
    def webhook_secret_token(self) -> Optional[str]:
        """Секретный токен для webhook"""
        return os.getenv('WEBHOOK_SECRET_TOKEN')
    
    # === DATABASE SETTINGS (для будущего использования) ===
    @property
    def database_url(self) -> Optional[str]:
        """URL базы данных"""
        return os.getenv('DATABASE_URL')
    
    @property
    def redis_url(self) -> Optional[str]:
        """URL Redis для кэширования"""
        return os.getenv('REDIS_URL')
    
    # === МЕТОДЫ ВАЛИДАЦИИ ===
    def _validate_required_env_vars(self):
        """Проверка обязательных переменных окружения"""
        required_vars = {
            'TELEGRAM_BOT_TOKEN': self.telegram_bot_token,
            'OPENAI_API_KEY': self.openai_api_key
        }
        
        missing_vars = []
        for var_name, var_value in required_vars.items():
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            error_msg = f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _setup_logging(self):
        """Настройка логирования"""
        # Удаляем стандартный обработчик loguru
        logger.remove()
        
        # Добавляем консольный обработчик
        logger.add(
            sink=lambda msg: print(msg, end=''),
            format=self.log_format,
            level=self.log_level,
            colorize=True
        )
        
        # Добавляем файловый обработчик если включен
        if self.log_file_enabled:
            os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
            logger.add(
                sink=self.log_file_path,
                format=self.log_format,
                level=self.log_level,
                rotation="1 day",
                retention="7 days",
                compression="zip"
            )
    
    def get_webhook_url(self) -> Optional[str]:
        """Получить полный URL для webhook"""
        if self.webhook_url:
            return self.webhook_url
        elif self.app_url:
            return f"{self.app_url.rstrip('/')}{self.webhook_path}"
        return None
    
    def is_production(self) -> bool:
        """Проверка, запущено ли приложение в продакшене"""
        return not (self.debug_mode or self.development_mode)
    
    def get_environment_info(self) -> dict:
        """Получить информацию о текущем окружении"""
        return {
            'debug_mode': self.debug_mode,
            'development_mode': self.development_mode,
            'production_mode': self.is_production(),
            'webhook_enabled': bool(self.get_webhook_url()),
            'keep_alive_enabled': self.keep_alive_enabled,
            'cache_enabled': self.cache_enabled,

            'log_level': self.log_level,
            'openai_model': self.openai_model,
            'translation_service': self.translation_service,
            'ocr_engine': self.ocr_engine
        }
    
    def validate_configuration(self) -> bool:
        """Валидация всей конфигурации"""
        try:
            # Проверка токенов
            if not self.telegram_bot_token.startswith('bot') and ':' not in self.telegram_bot_token:
                logger.warning("Telegram bot token может быть некорректным")
            
            if not self.openai_api_key.startswith('sk-'):
                logger.warning("OpenAI API key может быть некорректным")
            
            # Проверка портов
            if not (1 <= self.server_port <= 65535):
                logger.error(f"Некорректный порт сервера: {self.server_port}")
                return False
            
            # Проверка размеров
            if self.max_image_size <= 0:
                logger.error(f"Некорректный максимальный размер изображения: {self.max_image_size}")
                return False
            
            # Проверка интервалов
            if self.keep_alive_interval <= 0:
                logger.error(f"Некорректный интервал keep-alive: {self.keep_alive_interval}")
                return False
            
            logger.info("Конфигурация прошла валидацию")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка валидации конфигурации: {e}")
            return False
    
    def print_configuration(self):
        """Вывод текущей конфигурации (без секретных данных)"""
        config_info = {
            'Server': {
                'Host': self.server_host,
                'Port': self.server_port,
                'Webhook URL': self.get_webhook_url() or 'Not set (polling mode)',
                'Environment': 'Production' if self.is_production() else 'Development'
            },
            'OpenAI': {
                'Model': self.openai_model,
                'Max Tokens': self.openai_max_tokens,
                'Temperature': self.openai_temperature,
                'API Key': 'Set' if self.openai_api_key else 'Not set'
            },
            'Translation': {
                'Default Service': self.translation_service,
                'Source Language': self.default_source_language,
                'Target Language': self.default_target_language
            },
            'OCR': {
                'Engine': self.ocr_engine,
                'Languages': ', '.join(self.ocr_languages[:5]) + ('...' if len(self.ocr_languages) > 5 else ''),
                'Preprocessing': 'Enabled' if self.image_preprocessing_enabled else 'Disabled'
            },
            'Features': {
                'Keep Alive': 'Enabled' if self.keep_alive_enabled else 'Disabled',

                'Caching': 'Enabled' if self.cache_enabled else 'Disabled',
                'File Logging': 'Enabled' if self.log_file_enabled else 'Disabled'
            },
            'Limits': {
                'Max Image Size': f"{self.max_image_size // 1024 // 1024} MB",
                'Supported Formats': ', '.join(self.supported_image_formats),

            }
        }
        
        logger.info("=== КОНФИГУРАЦИЯ БОТА ===")
        for section, settings in config_info.items():
            logger.info(f"\n[{section}]")
            for key, value in settings.items():
                logger.info(f"  {key}: {value}")
        logger.info("=" * 30)

# Глобальный экземпляр конфигурации
config = None

def get_config() -> Config:
    """Получить глобальный экземпляр конфигурации"""
    global config
    if config is None:
        config = Config()
    return config

# Для удобства импорта
def load_config() -> Config:
    """Загрузить и валидировать конфигурацию"""
    cfg = get_config()
    
    if not cfg.validate_configuration():
        raise ValueError("Конфигурация содержит ошибки")
    
    if cfg.debug_mode:
        cfg.print_configuration()
    
    return cfg