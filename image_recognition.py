import cv2
import numpy as np
import torch
from ultralytics import YOLO
from typing import List, Dict, Tuple
import os
from loguru import logger

class ImageRecognizer:
    def __init__(self, model_path: str = 'D:/4 курс/Хакатон/Guide_Me2/GuideMe/museum_yolov8.pt'):
        """
        Инициализация распознавателя изображений с YOLO.

        :param model_path: Путь к предобученной модели YOLO (по умолчанию yolov8n.pt)
        """
        try:
            self.model = YOLO(model_path)
            logger.info(f"Модель YOLO загружена из {model_path}")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели YOLO: {e}")
            raise
        
        # Кэширование результатов для улучшения производительности
        self.cache: Dict[str, List[Dict]] = {}

    def recognize_image(self, image_path: str) -> List[Dict]:
        """
        Распознавание объектов на изображении.

        :param image_path: Путь к файлу изображения
        :return: Список распознанных объектов с их метаданными
        """
        if image_path in self.cache:
            logger.debug(f"Изображение {image_path} найдено в кэше")
            return self.cache[image_path]

        if not os.path.exists(image_path):
            logger.error(f"Файл изображения {image_path} не найден")
            raise FileNotFoundError(f"Файл {image_path} не найден")

        try:
            results = self.model(image_path, conf=0.01)
            logger.info(f"Распознавание выполнено для {image_path}")
        except Exception as e:
            logger.error(f"Ошибка при распознавании изображения {image_path}: {e}")
            raise

        recognized_objects = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                label = self.model.names[cls]
                
                recognized_objects.append({
                    'class': label,
                    'confidence': conf,
                    'coordinates': box.xyxy[0].tolist()
                })

        self.cache[image_path] = recognized_objects
        logger.debug(f"Результаты для {image_path} добавлены в кэш")
        return recognized_objects

    def match_with_exhibits(self, recognized_objects: List[Dict]) -> List[Tuple]:
        """
        Сопоставление распознанных объектов с экспонатами музея.

        :param recognized_objects: Список распознанных объектов
        :return: Список кортежей (объект, экспонат) для совпадений
        """
        from database import museum_database

        matches = []
        for obj in recognized_objects:
            exhibits = museum_database.search_exhibits(obj['class'])
            if exhibits:
                for exhibit in exhibits:
                    matches.append((obj, exhibit))
                    logger.info(f"Найдено совпадение: {obj['class']} -> {exhibit[2]}")
            else:
                logger.debug(f"Для объекта {obj['class']} экспонаты не найдены")

        return matches