import os
from googletrans import Translator, LANGUAGES
from loguru import logger
from typing import Optional, Dict, List, Tuple
import asyncio
from openai_handler import get_openai_handler

class TranslationHandler:
    def __init__(self):
        self.google_translator = Translator()
        self.openai_handler = get_openai_handler()
        
        # Настройки по умолчанию
        self.default_source_lang = os.getenv('DEFAULT_SOURCE_LANG', 'auto')
        self.default_target_lang = os.getenv('DEFAULT_TARGET_LANG', 'en')
        self.translation_service = os.getenv('TRANSLATION_SERVICE', 'google')
        
        # Маппинг языков для удобства пользователей
        self.language_mapping = {
            'русский': 'ru',
            'английский': 'en',
            'немецкий': 'de',
            'французский': 'fr',
            'испанский': 'es',
            'итальянский': 'it',
            'португальский': 'pt',
            'китайский': 'zh',
            'японский': 'ja',
            'корейский': 'ko',
            'арабский': 'ar',
            'турецкий': 'tr',
            'польский': 'pl',
            'украинский': 'uk',
            'чешский': 'cs',
            'голландский': 'nl',
            'шведский': 'sv',
            'норвежский': 'no',
            'датский': 'da',
            'финский': 'fi',
            'греческий': 'el',
            'венгерский': 'hu',
            'румынский': 'ro',
            'болгарский': 'bg',
            'хорватский': 'hr',
            'словацкий': 'sk',
            'словенский': 'sl',
            'эстонский': 'et',
            'латвийский': 'lv',
            'литовский': 'lt'
        }
        
        # Обратный маппинг
        self.reverse_language_mapping = {v: k for k, v in self.language_mapping.items()}
        
        logger.info(f"Переводчик инициализирован. Сервис: {self.translation_service}")
    
    def get_language_code(self, language: str) -> str:
        """
        Получить код языка из названия
        
        Args:
            language: Название языка на русском или код языка
        
        Returns:
            Код языка
        """
        language = language.lower().strip()
        
        # Если уже код языка
        if language in LANGUAGES.keys():
            return language
        
        # Если название на русском
        if language in self.language_mapping:
            return self.language_mapping[language]
        
        # Поиск по частичному совпадению
        for lang_name, lang_code in self.language_mapping.items():
            if language in lang_name or lang_name in language:
                return lang_code
        
        # По умолчанию возвращаем как есть
        return language
    
    def get_language_name(self, language_code: str) -> str:
        """
        Получить название языка из кода
        
        Args:
            language_code: Код языка
        
        Returns:
            Название языка на русском
        """
        language_code = language_code.lower().strip()
        
        if language_code in self.reverse_language_mapping:
            return self.reverse_language_mapping[language_code]
        
        # Если есть в Google Translate
        if language_code in LANGUAGES:
            return LANGUAGES[language_code].capitalize()
        
        return language_code.upper()
    
    async def translate_with_google(self, text: str, target_lang: str = 'ru', source_lang: str = 'auto') -> Optional[Dict]:
        """
        Перевод с помощью Google Translate
        
        Args:
            text: Текст для перевода
            target_lang: Целевой язык
            source_lang: Исходный язык
        
        Returns:
            Словарь с результатами перевода
        """
        try:
            # Конвертация названий языков в коды
            target_code = self.get_language_code(target_lang)
            source_code = self.get_language_code(source_lang) if source_lang != 'auto' else 'auto'
            
            # Выполнение перевода
            result = self.google_translator.translate(text, dest=target_code, src=source_code)
            
            translation_result = {
                'success': True,
                'translated_text': result.text,
                'source_language': self.get_language_name(result.src),
                'target_language': self.get_language_name(target_code),
                'source_language_code': result.src,
                'target_language_code': target_code,
                'service': 'Google Translate',
                'confidence': getattr(result, 'confidence', None)
            }
            
            logger.info(f"Google Translate: {result.src} -> {target_code}, длина: {len(result.text)}")
            return translation_result
            
        except Exception as e:
            logger.error(f"Ошибка Google Translate: {e}")
            return {
                'success': False,
                'error': str(e),
                'service': 'Google Translate'
            }
    
    async def translate_with_openai(self, text: str, target_lang: str = 'английский', source_lang: str = 'автоопределение') -> Optional[Dict]:
        """
        Перевод с помощью OpenAI GPT
        
        Args:
            text: Текст для перевода
            target_lang: Целевой язык
            source_lang: Исходный язык
        
        Returns:
            Словарь с результатами перевода
        """
        try:
            translated_text = await self.openai_handler.translate_text(text, target_lang, source_lang)
            
            if translated_text:
                # Определение исходного языка если нужно
                detected_lang = source_lang
                if source_lang in ['auto', 'автоопределение']:
                    detected_lang = await self.openai_handler.detect_language(text)
                    if not detected_lang:
                        detected_lang = 'неизвестный'
                
                translation_result = {
                    'success': True,
                    'translated_text': translated_text,
                    'source_language': detected_lang,
                    'target_language': target_lang,
                    'service': 'OpenAI GPT',
                    'confidence': 95  # GPT обычно дает качественные переводы
                }
                
                logger.info(f"OpenAI перевод: {detected_lang} -> {target_lang}")
                return translation_result
            else:
                return {
                    'success': False,
                    'error': 'OpenAI не смог выполнить перевод',
                    'service': 'OpenAI GPT'
                }
                
        except Exception as e:
            logger.error(f"Ошибка OpenAI перевода: {e}")
            return {
                'success': False,
                'error': str(e),
                'service': 'OpenAI GPT'
            }
    
    async def translate_text(self, text: str, target_lang: str = None, source_lang: str = 'auto', use_openai: bool = None) -> Dict:
        """
        Основной метод перевода текста
        
        Args:
            text: Текст для перевода
            target_lang: Целевой язык
            source_lang: Исходный язык
            use_openai: Использовать OpenAI вместо Google
        
        Returns:
            Словарь с результатами перевода
        """
        if not text or not text.strip():
            return {
                'success': False,
                'error': 'Пустой текст для перевода'
            }
        
        # Настройки по умолчанию
        if target_lang is None:
            target_lang = self.default_target_lang
        
        if source_lang is None:
            source_lang = self.default_source_lang
        
        # Выбор сервиса перевода
        if use_openai is None:
            use_openai = self.translation_service == 'openai'
        
        logger.info(f"Начинаю перевод текста (длина: {len(text)}) на {target_lang}")
        
        # Попытка перевода с основным сервисом
        if use_openai:
            result = await self.translate_with_openai(text, target_lang, source_lang)
        else:
            result = await self.translate_with_google(text, target_lang, source_lang)
        
        # Если основной сервис не сработал, пробуем альтернативный
        if not result.get('success'):
            logger.warning(f"Основной сервис не сработал, пробую альтернативный")
            
            if use_openai:
                result = await self.translate_with_google(text, target_lang, source_lang)
            else:
                result = await self.translate_with_openai(text, target_lang, source_lang)
        
        return result
    
    async def get_available_languages(self) -> Dict[str, str]:
        """
        Получить список доступных языков
        
        Returns:
            Словарь с языками {название: код}
        """
        return self.language_mapping.copy()
    
    async def detect_language(self, text: str) -> Optional[Dict]:
        """
        Определение языка текста
        
        Args:
            text: Текст для анализа
        
        Returns:
            Информация о языке
        """
        try:
            # Сначала пробуем Google
            detected = self.google_translator.detect(text)
            
            result = {
                'success': True,
                'language_code': detected.lang,
                'language_name': self.get_language_name(detected.lang),
                'confidence': detected.confidence,
                'service': 'Google Translate'
            }
            
            logger.info(f"Определен язык: {result['language_name']} ({result['language_code']})")
            return result
            
        except Exception as e:
            logger.warning(f"Google не смог определить язык: {e}")
            
            # Пробуем OpenAI
            try:
                language_name = await self.openai_handler.detect_language(text)
                if language_name:
                    return {
                        'success': True,
                        'language_name': language_name,
                        'language_code': self.get_language_code(language_name),
                        'confidence': 0.8,
                        'service': 'OpenAI GPT'
                    }
            except Exception as e2:
                logger.error(f"OpenAI тоже не смог определить язык: {e2}")
            
            return {
                'success': False,
                'error': 'Не удалось определить язык текста'
            }
    
    async def get_multiple_translations(self, text: str, target_languages: List[str]) -> Dict[str, Dict]:
        """
        Получить переводы на несколько языков
        
        Args:
            text: Текст для перевода
            target_languages: Список целевых языков
        
        Returns:
            Словарь с переводами для каждого языка
        """
        results = {}
        
        for lang in target_languages:
            try:
                result = await self.translate_text(text, lang)
                results[lang] = result
            except Exception as e:
                logger.error(f"Ошибка перевода на {lang}: {e}")
                results[lang] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def format_translation_result(self, result: Dict) -> str:
        """
        Форматирование результата перевода для отображения пользователю
        
        Args:
            result: Результат перевода
        
        Returns:
            Отформатированная строка
        """
        if not result.get('success'):
            return f"❌ Ошибка перевода: {result.get('error', 'Неизвестная ошибка')}"
        
        translated_text = result['translated_text']
        source_lang = result.get('source_language', 'неизвестный')
        target_lang = result.get('target_language', 'неизвестный')
        service = result.get('service', 'неизвестный сервис')
        
        formatted = f"🔄 **Перевод** ({source_lang} → {target_lang})\n\n"
        formatted += f"{translated_text}\n\n"
        formatted += f"_Переведено с помощью {service}_"
        
        return formatted

# Глобальный экземпляр переводчика
translation_handler = None

def get_translation_handler() -> TranslationHandler:
    """Получить глобальный экземпляр переводчика"""
    global translation_handler
    if translation_handler is None:
        translation_handler = TranslationHandler()
    return translation_handler