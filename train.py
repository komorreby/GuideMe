from ultralytics import YOLO
def main():
    # Загружаем предобученную модель
    model = YOLO("yolo11x.pt")  # Можно заменить на yolov8s.pt, yolov8m.pt для большей точности

    # Запускаем обучение
    results = model.train(
        data="C:\\Users\\alex\\Desktop\\GuideMe\\datasets\\data.yaml",
        epochs=100,
        imgsz=640,
        batch=8,
        name="museum_model11",
        patience=10,
        device=0,  # GPU
    )

    # Сохраняем модель
    model.save("C:\\Users\\alex\\Desktop\\GuideMe\\museum_yolov11.pt")
    
if __name__ == '__main__':
    main()

# from ultralytics import YOLO
# model = YOLO("C:\\Users\\alex\\Desktop\\GuideMe\\runs\\detect\\museum_model\\weights\\best.pt")  # Путь к вашей модели
# results = model.predict("test.jpg", conf=0.01)
# print(results[0].boxes)  # Должны быть bounding boxes