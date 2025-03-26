# from ultralytics import YOLO

# # Загружаем предобученную модель
# model = YOLO("yolov8n.pt")

# # Запускаем обучение
# model.train(data="/path/to/dataset/data.yaml", epochs=50, imgsz=640)

# # Сохраняем обученную модель
# model.save("museum_yolov8.pt")

#  from ultralytics import YOLO

# # Загружаем предобученную модель
# model = YOLO("yolov8n.pt")  # Можно заменить на yolov8s.pt, yolov8m.pt для большей точности

# # Запускаем обучение
# model.train(
#     data="C:\\Users\\alex\\Desktop\\GuideMe\\datasets\\data.yaml",  # Путь к вашему data.yaml
#     epochs=50,                                    # Количество эпох
#     imgsz=640,                                    # Размер изображения (обычно 640x640)
#     batch=16,                                     # Размер батча (зависит от вашей видеокарты)
#     name="museum_model",                          # Имя эксперимента
#     patience=10,                                  # Ранняя остановка, если нет улучшений
#                                   # GPU (0) или CPU (-1)
# )

# # Сохраняем модель
# model.save("C:\\Users\\alex\\Desktop\\GuideMe\\museum_yolov8.pt")

from ultralytics import YOLO
model = YOLO("C:\\Users\\alex\\Desktop\\GuideMe\\runs\\detect\\museum_model\\weights\\best.pt")  # Путь к вашей модели
results = model.predict("test.jpg", conf=0.01)
print(results[0].boxes)  # Должны быть bounding boxes