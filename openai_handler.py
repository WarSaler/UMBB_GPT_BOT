import os
import openai
from loguru import logger
from typing import Optional, Dict, Any

class OpenAIHandler:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
        
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        logger.info(f"OpenAI клиент инициализирован с моделью: {self.model}")
    
    async def translate_text(self, text: str, target_language: str = "русский", source_language: str = "автоопределение") -> Optional[str]:
        """
        Переводит текст с помощью OpenAI GPT
        
        Args:
            text: Текст для перевода
            target_language: Целевой язык перевода
            source_language: Исходный язык (по умолчанию автоопределение)
        
        Returns:
            Переведенный текст или None в случае ошибки
        """
        try:
            prompt = f"""
Ты профессиональный переводчик. Переведи следующий текст с языка "{source_language}" на "{target_language}".

Важно:
1. Сохрани оригинальную структуру и форматирование текста
2. Если это чек или документ, сохрани табличную структуру
3. Переведи только содержимое, сохранив числа, даты и специальные символы
4. Если встречаются названия брендов или собственные имена, оставь их без изменений

Текст для перевода:
{text}

Переведенный текст:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты профессиональный переводчик, который сохраняет структуру и форматирование оригинального текста."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content.strip()
            logger.info(f"Текст успешно переведен на {target_language}")
            return translated_text
            
        except Exception as e:
            logger.error(f"Ошибка при переводе текста: {e}")
            return None
    
    async def improve_ocr_text(self, ocr_text: str, context: str = "документ") -> Optional[str]:
        """
        Улучшает качество распознанного OCR текста с помощью GPT
        
        Args:
            ocr_text: Текст, полученный от OCR
            context: Контекст документа (чек, документ, письмо и т.д.)
        
        Returns:
            Улучшенный текст или None в случае ошибки
        """
        try:
            prompt = f"""
Ты эксперт по обработке текста. Исправь ошибки в тексте, полученном от системы оптического распознавания символов (OCR).

Контекст: {context}

Задачи:
1. Исправь орфографические ошибки
2. Восстанови правильную структуру и форматирование
3. Сохрани все числа, даты и специальные символы точно
4. Если это чек или таблица, восстанови табличную структуру
5. Удали артефакты OCR (лишние символы, неправильные переносы)

Исходный OCR текст:
{ocr_text}

Исправленный текст:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты эксперт по исправлению текста после OCR распознавания."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            improved_text = response.choices[0].message.content.strip()
            logger.info("OCR текст успешно улучшен")
            return improved_text
            
        except Exception as e:
            logger.error(f"Ошибка при улучшении OCR текста: {e}")
            return None
    
    async def detect_language(self, text: str) -> Optional[str]:
        """
        Определяет язык текста
        
        Args:
            text: Текст для определения языка
        
        Returns:
            Название языка или None в случае ошибки
        """
        try:
            prompt = f"""
Определи язык следующего текста. Ответь только названием языка на русском языке (например: "русский", "английский", "немецкий", "французский", "испанский", "китайский", "японский" и т.д.).

Текст: {text[:200]}...

Язык:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты эксперт по определению языков текста."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            language = response.choices[0].message.content.strip().lower()
            logger.info(f"Определен язык: {language}")
            return language
            
        except Exception as e:
            logger.error(f"Ошибка при определении языка: {e}")
            return None
    
    async def get_translation_suggestions(self, text: str) -> Dict[str, str]:
        """
        Получает варианты перевода на несколько популярных языков
        
        Args:
            text: Текст для перевода
        
        Returns:
            Словарь с переводами на разные языки
        """
        languages = {
            "Русский": "русский",
            "English": "английский", 
            "Español": "испанский",
            "Français": "французский",
            "Deutsch": "немецкий",
            "中文": "китайский"
        }
        
        translations = {}
        
        for lang_name, lang_full in languages.items():
            try:
                translation = await self.translate_text(text, lang_full)
                if translation:
                    translations[lang_name] = translation
            except Exception as e:
                logger.warning(f"Не удалось перевести на {lang_name}: {e}")
                continue
        
        return translations

# Глобальный экземпляр обработчика
openai_handler = None

def get_openai_handler() -> OpenAIHandler:
    """Получить глобальный экземпляр OpenAI обработчика"""
    global openai_handler
    if openai_handler is None:
        openai_handler = OpenAIHandler()
    return openai_handler