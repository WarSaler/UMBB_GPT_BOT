import os
import io
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from loguru import logger
from typing import Optional, List, Tuple, Dict
import re

class OCRHandler:
    def __init__(self):
        # Настройка путей для Tesseract
        tesseract_cmd = os.getenv('TESSERACT_CMD', '/usr/bin/tesseract')
        if os.path.exists(tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Используем только Tesseract для OCR
        logger.info("Используется Tesseract OCR")
        
        # Поддерживаемые форматы изображений
        self.supported_formats = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp']
        
        # Максимальный размер изображения (10MB)
        self.max_image_size = int(os.getenv('MAX_IMAGE_SIZE', 10485760))
        
        logger.info("OCR обработчик инициализирован")
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Предварительная обработка изображения для улучшения OCR
        
        Args:
            image: PIL изображение
        
        Returns:
            Обработанное изображение
        """
        try:
            # Конвертация в RGB если необходимо
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Увеличение контрастности
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Увеличение резкости
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Конвертация в оттенки серого
            image = image.convert('L')
            
            # Применение фильтра для уменьшения шума
            image = image.filter(ImageFilter.MedianFilter())
            
            # Увеличение размера изображения для лучшего распознавания
            width, height = image.size
            if width < 1000 or height < 1000:
                scale_factor = max(1000 / width, 1000 / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            logger.info("Изображение предварительно обработано")
            return image
            
        except Exception as e:
            logger.error(f"Ошибка при предварительной обработке изображения: {e}")
            return image
    
    def extract_text_tesseract(self, image: Image.Image, lang: str = 'rus+eng') -> Optional[str]:
        """
        Извлечение текста с помощью Tesseract OCR
        
        Args:
            image: PIL изображение
            lang: Языки для распознавания
        
        Returns:
            Распознанный текст или None
        """
        try:
            # Настройки Tesseract для лучшего распознавания
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя.,!?:;-+*/=()[]{}"№%$@#&<>|\\_ '
            
            text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
            
            if text.strip():
                logger.info(f"Tesseract распознал текст длиной {len(text)} символов")
                return text.strip()
            else:
                logger.warning("Tesseract не смог распознать текст")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка Tesseract OCR: {e}")
            return None
    

    
    def clean_text(self, text: str) -> str:
        """
        Очистка и нормализация распознанного текста
        
        Args:
            text: Сырой текст от OCR
        
        Returns:
            Очищенный текст
        """
        if not text:
            return ""
        
        # Удаление лишних пробелов и переносов строк
        text = re.sub(r'\s+', ' ', text)
        
        # Удаление артефактов OCR
        text = re.sub(r'[|\\~`]', '', text)
        
        # Исправление распространенных ошибок OCR
        replacements = {
            '0': 'О',  # Ноль вместо буквы О (в некоторых случаях)
            '1': 'I',  # Единица вместо I (в некоторых случаях)
            '5': 'S',  # Пятерка вместо S (в некоторых случаях)
        }
        
        # Применяем замены только если это выглядит как ошибка
        # (это упрощенная логика, в реальности нужен более сложный анализ)
        
        return text.strip()
    
    async def extract_text_from_image(self, image_data: bytes) -> Dict[str, any]:
        """
        Основной метод для извлечения текста из изображения
        
        Args:
            image_data: Байты изображения
        
        Returns:
            Словарь с результатами распознавания
        """
        result = {
            'success': False,
            'text': None,
            'method': None,
            'confidence': 0,
            'error': None
        }
        
        try:
            # Проверка размера файла
            if len(image_data) > self.max_image_size:
                result['error'] = f"Размер изображения превышает максимальный ({self.max_image_size} байт)"
                return result
            
            # Загрузка изображения
            image = Image.open(io.BytesIO(image_data))
            logger.info(f"Загружено изображение размером {image.size}")
            
            # Предварительная обработка
            processed_image = self.preprocess_image(image)
            
            # Распознавание с помощью Tesseract
            best_text = self.extract_text_tesseract(processed_image)
            best_method = 'Tesseract'
            
            if best_text:
                # Очистка текста
                cleaned_text = self.clean_text(best_text)
                
                result.update({
                    'success': True,
                    'text': cleaned_text,
                    'method': best_method,
                    'confidence': min(100, max(50, len(cleaned_text) * 2))  # Простая оценка уверенности
                })
                
                logger.info(f"Tesseract успешно распознал текст: {len(cleaned_text)} символов")
            else:
                result['error'] = 'Не удалось распознать текст на изображении'
                logger.warning("Tesseract не смог распознать текст")
            
            return result
            
        except Exception as e:
            error_msg = f"Ошибка при обработке изображения: {e}"
            logger.error(error_msg)
            result['error'] = error_msg
            return result
    
    def is_supported_format(self, filename: str) -> bool:
        """
        Проверка поддерживаемого формата файла
        
        Args:
            filename: Имя файла
        
        Returns:
            True если формат поддерживается
        """
        if not filename:
            return False
        
        extension = filename.lower().split('.')[-1]
        return extension in self.supported_formats

# Глобальный экземпляр обработчика
ocr_handler = None

def get_ocr_handler() -> OCRHandler:
    """Получить глобальный экземпляр OCR обработчика"""
    global ocr_handler
    if ocr_handler is None:
        ocr_handler = OCRHandler()
    return ocr_handler