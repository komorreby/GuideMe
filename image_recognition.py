import cv2
import numpy as np
import torch
from ultralytics import YOLO
from typing import List, Tuple, Dict, Optional
from database import museum_database
import os
from loguru import logger

class ImageRecognizer:
    def __init__(self, model_path: str = 'museum_yolov11.pt'):
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
            results = self.model(image_path, conf=0.1)
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
    

    def match_with_exhibits(self, recognized_objects: List[Dict], exact_match: bool = False) -> Optional[Tuple[Dict, Dict]]:
        """
        Сопоставление распознанного объекта с экспонатом музея, возвращает только первый результат с наибольшей уверенностью.

        :param recognized_objects: Список словарей с информацией о распознанных объектах.
                                Каждый словарь должен содержать ключи 'class' (str) и 'confidence' (float).
        :param exact_match: Если True, ищет только точные совпадения по названию (title).
                            Если False, использует поиск по всем полям (title, artist, description, tags).
        :return: Кортеж (распознанный объект, соответствующий экспонат) с наибольшей уверенностью или None, если совпадений нет.
        """
        if not recognized_objects:
            logger.debug("Список распознанных объектов пуст")
            return None

        # Сортируем по убыванию уверенности и берём первый элемент
        best_object = sorted(
            recognized_objects,
            key=lambda x: float(x.get('confidence', 0.0)),
            reverse=True
        )[0]
        class_name = best_object.get('class', '').strip()

        if not class_name:
            logger.warning(f"Объект с наибольшей уверенностью не содержит класса: {best_object}")
            return None

        logger.debug(f"Поиск экспоната для класса: '{class_name}' (confidence={best_object.get('confidence', 'N/A')}, exact_match={exact_match})")

        try:
            if exact_match:
                # Точный поиск только по полю 'title'
                exhibits = [ex for ex in museum_database.search_exhibits(class_name) 
                        if ex.get('title', '').lower() == class_name.lower()]
            else:
                # Поиск по всем полям (title, artist, description, tags)
                exhibits = museum_database.search_exhibits(class_name)

            logger.debug(f"Найдено {len(exhibits)} экспонатов для класса '{class_name}'")

            if exhibits:
                # Берём первый найденный экспонат
                exhibit = exhibits[0]
                logger.info(f"Совпадение: '{class_name}' -> '{exhibit['title']}' "
                        f"(уверенность: {best_object.get('confidence', 'N/A')})")
                return (best_object, exhibit)
            
            logger.debug(f"Для объекта '{class_name}' экспонаты не найдены")
            return None

        except Exception as e:
            logger.error(f"Ошибка при поиске экспонатов для '{class_name}': {type(e).__name__}: {str(e)}")
            return None