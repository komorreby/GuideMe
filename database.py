import sqlite3
import csv
from typing import List, Tuple

class MuseumDatabase:
    def __init__(self, db_path="art_museum.db"):
        """Инициализация базы данных музея искусств."""
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._populate_initial_data()

    def _create_tables(self):
        """Создание таблиц для музея искусств."""
        self.cursor.executescript('''
            -- Таблица залов
            CREATE TABLE IF NOT EXISTS halls (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                location TEXT,
                size INTEGER,           -- Площадь зала в кв.м
                art_period TEXT,        -- Художественный период (например, "Ренессанс")
                exhibit_count INTEGER DEFAULT 0
            );

            -- Таблица экспонатов (произведений искусства)
            CREATE TABLE IF NOT EXISTS exhibits (
                id INTEGER PRIMARY KEY,
                hall_id INTEGER,
                title TEXT NOT NULL,    -- Название произведения
                artist TEXT,            -- Автор
                description TEXT,
                art_style TEXT,         -- Стиль (например, "Импрессионизм")
                creation_year INTEGER,  -- Год создания
                medium TEXT,            -- Материал/техника (например, "Масло на холсте")
                origin_country TEXT,    -- Страна происхождения
                tags TEXT,              -- Теги для поиска
                multimedia_link TEXT,   -- Ссылка на фото/видео
                FOREIGN KEY(hall_id) REFERENCES halls(id)
            );
            -- Таблица маршрутов
            CREATE TABLE IF NOT EXISTS routes (
            from_node TEXT,
            to_node TEXT,
            distance REAL,
            FOREIGN KEY (from_node) REFERENCES rooms (id),
            FOREIGN KEY (to_node) REFERENCES rooms (id)
            );
            

            -- Таблица FAQ и знаний музея
            CREATE TABLE IF NOT EXISTS museum_knowledge (
                id INTEGER PRIMARY KEY,
                category TEXT,
                question TEXT,
                answer TEXT,
                keywords TEXT
            );
        ''')
        self.conn.commit()

    def _populate_initial_data(self):
        """Заполнение базы начальными данными для музея искусств."""
        # Залы
        initial_halls = [
            (1, "Зал Фойе", "Входная зона музея, где посетители могут ознакомиться с основными экспозициями.", "Первый этаж", 200, "Ренессанс", 10),
            (2, "Зал Ренессанса", "Произведения великих мастеров эпохи Возрождения, таких как Леонардо да Винчи и Микеланджело.", "Первый этаж", 250, "Ренессанс", 15),
            (3, "Зал Барокко", "Искусство барокко с его драматическими композициями и яркими цветами.", "Первый этаж", 180, "Барокко", 12),
            (4, "Зал Рококо", "Легкие и изящные произведения рококо, отражающие утонченность и игривость стиля.", "Первый этаж", 180, "Рококо", 12),
            (5, "Зал Классицизма", "Классические произведения, вдохновленные античностью и строгими формами.", "Первый этаж", 180, "Классицизм", 12),
            (6, "Зал Романтизма", "Эмоциональные и выразительные работы романтиков, подчеркивающие индивидуальность и природу.", "Первый этаж", 180, "Романтизм", 12),
            (7, "Зал Импрессионизма", "Яркие и живые картины импрессионистов, запечатлевающие мгновения и свет.", "Первый этаж", 180, "Импрессионизм", 12),
            (8, "Зал Постимпрессионизма", "Работы постимпрессионистов, исследующих цвет и форму, такие как Ван Гог и Сезанн.", "Первый этаж", 180, "Постимпрессионизм", 12),
            (9, "Зал Модернизма", "Экспериментальные и новаторские произведения модернистов, отражающие изменения в обществе.", "Первый этаж", 180, "Модернизм", 12),
            (10, "Зал Сюрреализма", "Сюрреалистические работы, исследующие подсознание и сны, такие как картины Дали.", "Первый этаж", 180, "Сюрреализм", 12)
        ]   

        routes = [
            ('1', '2', 1),  
            ('2', '3', 1),  
            ('3', '4', 1), 
            ('3', '9', 1),  
            ('4', '5', 1),  
            ('5', '6', 1),  
            ('6', '7', 1),  
            ('7', '8', 1),  
            ('8', '9', 1),  
            ('8', '10', 1), 
            ('9', '8', 1),  
        ]
        
        # Экспонаты
        initial_exhibits = [
            (1, 1, "Мона Лиза", "Леонардо да Винчи", "Знаменитая картина с загадочной улыбкой", "Ренессанс", 1503, "Масло на тополе", "Италия", "портрет, ренессанс, леонардо", "mona_lisa.jpg"),
            (2, 1, "Тайная вечеря", "Леонардо да Винчи", "Фреска с изображением последней трапезы", "Ренессанс", 1498, "Темпера на штукатурке", "Италия", "фреска, религия", "last_supper.jpg"),
            (3, 2, "Звёздная ночь", "Винсент Ван Гог", "Пейзаж с вихрями звёзд", "Постимпрессионизм", 1889, "Масло на холсте", "Нидерланды", "пейзаж, ван гог", "starry_night.jpg"),
            (4, 2, "Герника", "Пабло Пикассо", "Антивоенное произведение", "Кубизм", 1937, "Масло на холсте", "Испания", "война, кубизм", "guernica.jpg"),
            (5, 3, "Великая волна в Канагаве", "Хокусай", "Гравюра с изображением волны", "Укиё-э", 1831, "Ксилография", "Япония", "гравюра, море", "great_wave.jpg")
        ]

        # FAQ
        initial_knowledge = [
            (1, "museum_info", "Когда основан музей?", "Музей искусств открыт в 1920 году", "музей, история"),
            (2, "exhibit_info", "Что такое 'Мона Лиза'?", "Картина Леонардо да Винчи, созданная в 1503 году", "мона лиза, ренессанс"),
            (3, "tour_info", "Сколько длится экскурсия?", "Экскурсия длится 1-2 часа", "экскурсия, время")
        ]

        self.cursor.executemany(
            "INSERT OR IGNORE INTO halls VALUES (?, ?, ?, ?, ?, ?, ?)", initial_halls
        )
        self.cursor.executemany(
        "INSERT OR IGNORE INTO routes VALUES (?, ?, ?)", routes
        )
        self.cursor.executemany(
            "INSERT OR IGNORE INTO exhibits VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", initial_exhibits
        )
        self.cursor.executemany(
            "INSERT OR IGNORE INTO museum_knowledge VALUES (?, ?, ?, ?, ?)", initial_knowledge
        )
        self.conn.commit()

    def load_from_csv(self, table_name: str, csv_path: str):
        """
        Загрузка данных из CSV-файла в указанную таблицу.
        
        :param table_name: Название таблицы ('halls', 'exhibits', 'museum_knowledge')
        :param csv_path: Путь к CSV-файлу
        """
        try:
            with open(csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                if table_name == "halls":
                    query = "INSERT OR REPLACE INTO halls (id, name, description, location, size, art_period, exhibit_count) VALUES (?, ?, ?, ?, ?, ?, ?)"
                    data = [
                        (row["id"], row["name"], row["description"], row["location"], row["size"], row["art_period"], row["exhibit_count"])
                        for row in reader
                    ]
                elif table_name == "exhibits":
                    query = "INSERT OR REPLACE INTO exhibits (id, hall_id, title, artist, description, art_style, creation_year, medium, origin_country, tags, multimedia_link) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    data = [
                        (row["id"], row["hall_id"], row["title"], row["artist"], row["description"], row["art_style"],
                         row["creation_year"], row["medium"], row["origin_country"], row["tags"], row["multimedia_link"])
                        for row in reader
                    ]
                elif table_name == "museum_knowledge":
                    query = "INSERT OR REPLACE INTO museum_knowledge (id, category, question, answer, keywords) VALUES (?, ?, ?, ?, ?)"
                    data = [
                        (row["id"], row["category"], row["question"], row["answer"], row["keywords"])
                        for row in reader
                    ]
                else:
                    raise ValueError(f"Неизвестная таблица: {table_name}")

                self.cursor.executemany(query, data)
                self.conn.commit()
                print(f"Данные успешно загружены в таблицу {table_name} из {csv_path}")
        except Exception as e:
            print(f"Ошибка загрузки CSV: {e}")
            self.conn.rollback()

    def get_hall_info(self, hall_id: int) -> Tuple:
        """Получение информации о зале по ID."""
        self.cursor.execute("SELECT * FROM halls WHERE id = ?", (hall_id,))
        return self.cursor.fetchone()

    def get_exhibit_info(self, exhibit_id: int) -> Tuple:
        """Получение информации об экспонате по ID."""
        self.cursor.execute("SELECT * FROM exhibits WHERE id = ?", (exhibit_id,))
        return self.cursor.fetchone()

    def search_exhibits(self, keywords: str) -> List[Tuple]:
        """Поиск экспонатов по ключевым словам."""
        self.cursor.execute(
            "SELECT * FROM exhibits WHERE tags LIKE ? OR title LIKE ? OR artist LIKE ? OR description LIKE ?",
            (f"%{keywords}%", f"%{keywords}%", f"%{keywords}%", f"%{keywords}%")
        )
        return self.cursor.fetchall()

    def get_faq(self, category: str = None) -> List[Tuple]:
        """Получение FAQ по категории или всех записей."""
        query = "SELECT question, answer FROM museum_knowledge"
        params = ()
        if category:
            query += " WHERE category = ?"
            params = (category,)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        """Закрытие соединения с базой данных."""
        self.conn.close()

# Глобальная инициализация базы данных
museum_database = MuseumDatabase()

# Пример использования загрузки из CSV (раскомментируйте для теста)
# museum_database.load_from_csv("exhibits", "exhibits.csv")