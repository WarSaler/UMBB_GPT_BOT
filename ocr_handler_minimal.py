#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Минимальная версия OCR handler для тестирования
"""

import os
from typing import Optional, Dict, Any
from io import BytesIO

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.info = print
    logger.error = print
    logger.warning = print

class MinimalOCRHandler:
    """Минимальная версия OCR обработчика"""
    
    def __init__(self):
        self.supported_formats = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp']
        logger.info("Минимальный OCR handler инициализирован")
    
    async def extract_text_from_image(self, image_data: bytes, language: str = 'rus+eng') -> str:
        """Заглушка для извлечения текста из изображения"""
        logger.info(f"Извлечение текста из изображения (язык: {language})")
        logger.info(f"Размер изображения: {len(image_data)} байт")
        
        # Заглушка - возвращаем тестовый текст
        return "[OCR РЕЗУЛЬТАТ] Это тестовый текст, извлеченный из изображения. OCR функция временно недоступна."
    
    def is_supported_format(self, filename: str) -> bool:
        """Проверка поддерживаемого формата"""
        if not filename:
            return False
        
        extension = filename.lower().split('.')[-1]
        return extension in self.supported_formats
    
    async def preprocess_image(self, image_data: bytes) -> bytes:
        """Заглушка для предобработки изображения"""
        logger.info("Предобработка изображения")
        return image_data

def get_ocr_handler():
    """Получить экземпляр OCR обработчика"""
    try:
        return MinimalOCRHandler()
    except Exception as e:
        logger.error(f"Ошибка создания OCR handler: {e}")
        return None