import sqlite3
from typing import List, Dict
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, db_path: str = "art_museum.db"):
        """
        Инициализация загрузчика данных.
        
        Args:
            db_path (str): Путь к файлу базы данных
        """
        self.db_path = db_path

    def _load_exhibits_data(self) -> List[Dict]:
        """Возвращает данные об экспонатах для инициализации."""
        return [
            {"id": 1, "hall_id": 1, "title": "The Last Supper", "artist": "Leonardo da Vinci",
            "description": "Иисус с апостолами во время Тайной Вечери", "art_style": "Renaissance",
            "creation_year": 1495, "medium": "Фреска", "origin_country": "Италия",
            "tags": "религия", "multimedia_link": "last_supper.jpg"},
            
            {"id": 2, "hall_id": 1, "title": "Sistine Madonna", "artist": "Raphael",
            "description": "Мадонна с младенцем и ангелами", "art_style": "Renaissance",
            "creation_year": 1512, "medium": "Масло на холсте", "origin_country": "Италия",
            "tags": "религия", "multimedia_link": "sistine_madonna.jpg"},
            
            {"id": 3, "hall_id": 1, "title": "The Birth of Venus", "artist": "Sandro Botticelli",
            "description": "Рождение богини Венеры из морской пены", "art_style": "Renaissance",
            "creation_year": 1486, "medium": "Темпера на холсте", "origin_country": "Италия",
            "tags": "мифология, обнажённая", "multimedia_link": "birth_of_venus.jpg"},
            
            {"id": 4, "hall_id": 2, "title": "Madonna of Loreto", "artist": "Caravaggio",
            "description": "Дева Мария с младенцем и двумя паломниками", "art_style": "Baroque",
            "creation_year": 1604, "medium": "Масло на холсте", "origin_country": "Италия",
            "tags": "религия", "multimedia_link": "madonna_loreto.jpg"},
            
            {"id": 5, "hall_id": 2, "title": "The Triumph of Bacchus", "artist": "Peter Paul Rubens",
            "description": "Бахус и его спутники в пьяном веселье", "art_style": "Baroque",
            "creation_year": 1628, "medium": "Масло на холсте", "origin_country": "Фландрия",
            "tags": "мифология", "multimedia_link": "triumph_bacchus.jpg"},
            
            {"id": 6, "hall_id": 2, "title": "Venus and Mars", "artist": "Sandro Botticelli",
            "description": "Бог войны и богиня любви в безмятежности", "art_style": "Baroque",
            "creation_year": 1485, "medium": "Темпера на холсте", "origin_country": "Италия",
            "tags": "мифология, любовь", "multimedia_link": "venus_mars.jpg"},
            
            {"id": 7, "hall_id": 3, "title": "The Swing", "artist": "Jean-Honoré Fragonard",
            "description": "Девушка качается на качелях, мужчина любуется ею", "art_style": "Rococo",
            "creation_year": 1767, "medium": "Масло на холсте", "origin_country": "Франция",
            "tags": "романтика, легкость", "multimedia_link": "the_swing.jpg"},
            
            {"id": 8, "hall_id": 3, "title": "Judith Slaying Holofernes", "artist": "Artemisia Gentileschi",
            "description": "Юдифь убивает Олоферна", "art_style": "Rococo",
            "creation_year": 1614, "medium": "Масло на холсте", "origin_country": "Италия",
            "tags": "библейская сцена, жестокость", "multimedia_link": "judith_holofernes.jpg"},
            
            {"id": 9, "hall_id": 3, "title": "Self-Portrait with a Monkey", "artist": "Élisabeth Vigée Le Brun",
            "description": "Художница с обезьянкой", "art_style": "Rococo",
            "creation_year": 1790, "medium": "Масло на холсте", "origin_country": "Франция",
            "tags": "портрет", "multimedia_link": "self_portrait_monkey.jpg"},
            
            {"id": 10, "hall_id": 4, "title": "Olympia", "artist": "Édouard Manet",
            "description": "Обнажённая женщина лежит на кушетке", "art_style": "Neoclassicism",
            "creation_year": 1863, "medium": "Масло на холсте", "origin_country": "Франция",
            "tags": "обнажённая, реализм", "multimedia_link": "olympia.jpg"},
            
            {"id": 11, "hall_id": 4, "title": "The Oath of the Horatii", "artist": "Jacques-Louis David",
            "description": "Трое братьев клянутся сражаться", "art_style": "Neoclassicism",
            "creation_year": 1784, "medium": "Масло на холсте", "origin_country": "Франция",
            "tags": "история", "multimedia_link": "oath_horatii.jpg"},
            
            {"id": 12, "hall_id": 4, "title": "The Death of Socrates", "artist": "Jacques-Louis David",
            "description": "Смерть философа Сократа", "art_style": "Neoclassicism",
            "creation_year": 1787, "medium": "Масло на холсте", "origin_country": "Франция",
            "tags": "философия, история", "multimedia_link": "death_socrates.jpg"},
            
            {"id": 13, "hall_id": 5, "title": "Liberty Leading the People", "artist": "Eugène Delacroix",
            "description": "Аллегория Свободы, ведущая народ", "art_style": "Romanticism",
            "creation_year": 1830, "medium": "Масло на холсте", "origin_country": "Франция",
            "tags": "революция, аллегория", "multimedia_link": "liberty_leading.jpg"},
            
            {"id": 14, "hall_id": 5, "title": "The Raft of the Medusa", "artist": "Théodore Géricault",
            "description": "Выжившие после кораблекрушения на плоту", "art_style": "Romanticism",
            "creation_year": 1819, "medium": "Масло на холсте", "origin_country": "Франция",
            "tags": "драма, история", "multimedia_link": "raft_medusa.jpg"},
            
            {"id": 15, "hall_id": 5, "title": "Wanderer above the Sea of Fog", "artist": "Caspar David Friedrich",
            "description": "Человек стоит на вершине горы, любуясь пейзажем", "art_style": "Romanticism",
            "creation_year": 1818, "medium": "Масло на холсте", "origin_country": "Германия",
            "tags": "пейзаж, философия", "multimedia_link": "wanderer_fog.jpg"},
            
            {"id": 16, "hall_id": 6, "title": "Impression Sunrise", "artist": "Claude Monet",
            "description": "Рассвет в порту Гавра", "art_style": "Impressionism",
            "creation_year": 1872, "medium": "Масло на холсте", "origin_country": "Франция",
            "tags": "пейзаж", "multimedia_link": "impression_sunrise.jpg"},
            
            {"id": 17, "hall_id": 6, "title": "Ballet Rehearsal", "artist": "Edgar Degas",
            "description": "Танцовщицы балета на репетиции", "art_style": "Impressionism",
            "creation_year": 1873, "medium": "Масло на холсте", "origin_country": "Франция",
            "tags": "танец, балет", "multimedia_link": "ballet_rehearsal.jpg"},
            
            {"id": 18, "hall_id": 6, "title": "Luncheon of the Boating Party", "artist": "Pierre-Auguste Renoir",
            "description": "Обед на лодке с друзьями", "art_style": "Impressionism",
            "creation_year": 1881, "medium": "Масло на холсте", "origin_country": "Франция",
            "tags": "жанровая сцена", "multimedia_link": "boating_party.jpg"},
            
            {"id": 19, "hall_id": 7, "title": "The Starry Night", "artist": "Vincent van Gogh",
            "description": "Звёздная ночь над Сен-Реми", "art_style": "Post-Impressionism",
            "creation_year": 1889, "medium": "Масло на холсте", "origin_country": "Нидерланды",
            "tags": "пейзаж, эмоции", "multimedia_link": "starry_night.jpg"},
            
            {"id": 20, "hall_id": 7, "title": "The Card Players", "artist": "Paul Cézanne",
            "description": "Крестьяне за игрой в карты", "art_style": "Post-Impressionism",
            "creation_year": 1895, "medium": "Масло на холсте", "origin_country": "Франция",
            "tags": "жанровая сцена", "multimedia_link": "card_players.jpg"},
            
            {"id": 21, "hall_id": 7, "title": "Where Do We Come From? What Are We? Where Are We Going?", 
            "artist": "Paul Gauguin", "description": "Философская аллегория о жизни", "art_style": "Post-Impressionism",
            "creation_year": 1897, "medium": "Масло на холсте", "origin_country": "Франция",
            "tags": "философия, символизм", "multimedia_link": "gauguin_philosophy.jpg"},
            
            {"id": 22, "hall_id": 8, "title": "Les Demoiselles d'Avignon", "artist": "Pablo Picasso",
            "description": "Пять женщин в кубистическом стиле", "art_style": "Modernism",
            "creation_year": 1907, "medium": "Масло на холсте", "origin_country": "Испания",
            "tags": "кубизм, портрет", "multimedia_link": "demoiselles_avignon.jpg"},
            
            {"id": 23, "hall_id": 8, "title": "The Persistence of Memory", "artist": "Salvador Dalí",
            "description": "Растекающиеся часы в пустыне", "art_style": "Modernism",
            "creation_year": 1931, "medium": "Масло на холсте", "origin_country": "Испания",
            "tags": "сюрреализм", "multimedia_link": "persistence_memory.jpg"},
            
            {"id": 24, "hall_id": 8, "title": "Broadway Boogie Woogie", "artist": "Piet Mondrian",
            "description": "Абстракция в стиле нео-пластицизма", "art_style": "Modernism",
            "creation_year": 1942, "medium": "Масло на холсте", "origin_country": "Нидерланды",
            "tags": "абстракция", "multimedia_link": "broadway_boogie.jpg"},
            
            {"id": 25, "hall_id": 9, "title": "Campbell's Soup Cans", "artist": "Andy Warhol",
            "description": "32 банки супа Кэмпбелл", "art_style": "Contemporary",
            "creation_year": 1962, "medium": "Шёлкография", "origin_country": "США",
            "tags": "поп-арт", "multimedia_link": "campbell_soup.jpg"},
            
            {"id": 26, "hall_id": 9, "title": "Balloon Dog", "artist": "Jeff Koons",
            "description": "Гигантская собака из шариков", "art_style": "Contemporary",
            "creation_year": 1994, "medium": "Полированная сталь", "origin_country": "США",
            "tags": "скульптура, китч", "multimedia_link": "balloon_dog.jpg"},
            
            {"id": 27, "hall_id": 9, "title": "Untitled", "artist": "Jean-Michel Basquiat",
            "description": "Граффити-искусство с абстрактными фигурами", "art_style": "Contemporary",
            "creation_year": 1981, "medium": "Акрил на холсте", "origin_country": "США",
            "tags": "уличное искусство, экспрессионизм", "multimedia_link": "basquiat_untitled.jpg"}
        ]

    def _load_halls_data(self) -> List[Dict]:
        """Возвращает данные о залах для инициализации."""
        return [
            {"id": 1, "name": "Зал Фойе", "description": "Входная зона музея, где посетители могут ознакомиться с основными экспозициями",
             "location": "Первый этаж", "size": 200, "art_period": "Фойе", "exhibit_count": 0},
            {"id": 2, "name": "Зал Ренессанса", "description": "Произведения эпохи Возрождения",
             "location": "Первый этаж", "size": 200, "art_period": "Ренессанс", "exhibit_count": 3},
            {"id": 3, "name": "Зал Барокко", "description": "Искусство эпохи Барокко",
             "location": "Второй этаж", "size": 220, "art_period": "Барокко", "exhibit_count": 3},
            {"id": 4, "name": "Зал Рококо", "description": "Коллекция искусства Рококо",
             "location": "Третий этаж", "size": 180, "art_period": "Рококо", "exhibit_count": 3},
            {"id": 5, "name": "Зал Классицизма", "description": "Произведения эпохи Классицизма",
             "location": "Первый этаж", "size": 200, "art_period": "Классицизм", "exhibit_count": 3},
            {"id": 6, "name": "Зал Романтизма", "description": "Искусство эпохи Романтизма",
             "location": "Третий этаж", "size": 210, "art_period": "Романтизм", "exhibit_count": 3},
            {"id": 7, "name": "Зал Импрессионизма", "description": "Коллекция импрессионизма",
             "location": "Первый этаж", "size": 230, "art_period": "Импрессионизм", "exhibit_count": 3},
            {"id": 8, "name": "Зал Постимпрессионизма", "description": "Произведения постимпрессионизма",
             "location": "Второй этаж", "size": 200, "art_period": "Постимпрессионизм", "exhibit_count": 3},
            {"id": 9, "name": "Зал Модернизма", "description": "Искусство XX века",
             "location": "Второй этаж", "size": 250, "art_period": "Модернизм", "exhibit_count": 3},
            {"id": 10, "name": "Зал Сюрреализма", "description": "Коллекция сюрреализма",
             "location": "Третий этаж", "size": 190, "art_period": "Сюрреализм", "exhibit_count": 3}
        ]
    
    def _load_knowledge_data(self) -> List[Dict]:
            """Возвращает данные для таблицы museum_knowledge."""
            return [
                {"id": 1, "category": "museum_info", "question": "Когда основан музей?", 
                "answer": "Музей искусств открыт в 1920 году", "keywords": "музей, история"},
                {"id": 2, "category": "exhibit_info", "question": "Что такое 'Герника'?", 
                "answer": "Антивоенная картина Пабло Пикассо, созданная в 1937 году", "keywords": "герника, кубизм"},
                {"id": 3, "category": "tour_info", "question": "Сколько длится экскурсия?", 
                "answer": "Экскурсия длится 1-2 часа", "keywords": "экскурсия, время"},
                {"id": 4, "category": "hall_info", "question": "Сколько залов в музее?", 
                "answer": "В музее 10 залов, охватывающих разные эпохи искусства", "keywords": "залы, музей"},
                {"id": 5, "category": "exhibit_info", "question": "Что такое 'Звёздная ночь'?", 
                "answer": "Картина Винсента ван Гога с вихреобразным небом, 1889 год", "keywords": "звёздная ночь, постимпрессионизм"},
                {"id": 6, "category": "tour_info", "question": "Сколько длится экскурсия?", 
                "answer": "Стандартная экскурсия длится 1,5-2 часа, но есть экспресс-туры на 45 минут и углублённые на 3 часа", "keywords": "экскурсия, время"},
                {"id": 7, "category": "tour_info", "question": "Есть ли экскурсии на иностранных языках?", 
                "answer": "Да, доступны экскурсии на английском, французском и испанском по предварительной записи", "keywords": "экскурсия, языки"},
                {"id": 8, "category": "tour_info", "question": "Можно ли заказать индивидуальную экскурсию?", 
                "answer": "Да, индивидуальные экскурсии доступны по запросу, стоимость зависит от продолжительности и языка", "keywords": "экскурсия, индивидуально"},
                {"id": 9, "category": "exhibit_info", "question": "Что такое 'Герника'?", 
                "answer": "Антивоенная картина Пабло Пикассо (1937) в стиле кубизма, созданная в ответ на бомбардировку города Герника", "keywords": "герника, кубизм"},
                {"id": 10, "category": "exhibit_info", "question": "Что такое 'Звёздная ночь'?", 
                "answer": "Картина Винсента ван Гога (1889) в стиле постимпрессионизма, изображающая ночное небо с вихрями звёзд", "keywords": "звёздная ночь, постимпрессионизм"},
                {"id": 11, "category": "exhibit_info", "question": "Почему 'Олимпия' вызвала скандал?", 
                "answer": "Картина Эдуарда Мане (1863) шокировала публику откровенным изображением обнажённой женщины", "keywords": "олимпия, классицизм"},
                {"id": 12, "category": "exhibit_info", "question": "Что изображено на 'Свободе на баррикадах'?", 
                "answer": "Работа Эжена Делакруа (1830) символизирует революцию 1830 года во Франции", "keywords": "свобода на баррикадах, романтизм"},
                {"id": 13, "category": "exhibit_info", "question": "Что символизируют мягкие часы в 'Постоянстве памяти'?", 
                "answer": "В картине Сальвадора Дали (1931) мягкие часы отражают текучесть времени и сны", "keywords": "постоянство памяти, сюрреализм"},
                {"id": 14, "category": "exhibit_info", "question": "Какова идея 'Танца' Матисса?", 
                "answer": "Картина Анри Матисса (1910) передаёт радость движения и гармонию", "keywords": "танец, постимпрессионизм"},
                {"id": 15, "category": "hall_info", "question": "Чем отличается Зал Импрессионизма?", 
                "answer": "Зал Импрессионизма выделяется светлыми тонами и акцентом на мимолётных впечатлениях", "keywords": "импрессионизм, зал"},
                {"id": 16, "category": "hall_info", "question": "Что особенного в Зале Сюрреализма?", 
                "answer": "Зал Сюрреализма погружает в мир подсознания с необычными образами", "keywords": "сюрреализм, зал"}
            ]

    def _load_routes_data(self) -> List[Dict]:
        """Возвращает данные о маршрутах между залами."""
        return [
            {"from_node": "1", "to_node": "2", "distance": 1.0},
            {"from_node": "2", "to_node": "3", "distance": 1.0},
            {"from_node": "3", "to_node": "4", "distance": 1.0},
            {"from_node": "3", "to_node": "9", "distance": 1.0},
            {"from_node": "4", "to_node": "5", "distance": 1.0},
            {"from_node": "5", "to_node": "6", "distance": 1.0},
            {"from_node": "6", "to_node": "7", "distance": 1.0},
            {"from_node": "7", "to_node": "8", "distance": 1.0},
            {"from_node": "8", "to_node": "9", "distance": 1.0},
            {"from_node": "8", "to_node": "10", "distance": 1.0},  # Предполагаю, что "10" — ошибка, заменю на "0" (Фойе)
            {"from_node": "9", "to_node": "8", "distance": 1.0}
        ]

    def _load_feedback_data(self) -> List[Dict]:
        """Возвращает примерные данные обратной связи."""
        current_time = datetime.now().isoformat()
        return [
            {"user_id": 12345, "rating": 5, "feedback": "Отличный музей, экскурсия была увлекательной!", "timestamp": current_time},
            {"user_id": 67890, "rating": 4, "feedback": "Хорошая коллекция, но мало информации на английском", "timestamp": current_time},
            {"user_id": 54321, "rating": 3, "feedback": "Залы интересные, но было слишком шумно", "timestamp": current_time}
        ]

    def _load_bookings_data(self) -> List[Dict]:
        """Возвращает примерные данные о бронированиях."""
        current_time = datetime.now().isoformat()
        return [
            {"user_id": 12345, "time_slot": "10:00-11:30", "date": "2025-03-28", "timestamp": current_time},
            {"user_id": 67890, "time_slot": "14:00-15:00", "date": "2025-03-29", "timestamp": current_time},
            {"user_id": 54321, "time_slot": "16:00-18:00", "date": "2025-03-30", "timestamp": current_time}
        ]
    
    def initialize_database(self):
        """Инициализация базы данных начальными данными."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                
                # Очищаем таблицы перед загрузкой новых данных
                cursor.execute("DELETE FROM exhibits")
                cursor.execute("DELETE FROM halls")
                cursor.execute("DELETE FROM museum_knowledge")
                cursor.execute("DELETE FROM routes")
                cursor.execute("DELETE FROM feedback")
                cursor.execute("DELETE FROM bookings")
                
                # Загружаем данные о залах
                halls_data = self._load_halls_data()
                cursor.executemany(
                    '''INSERT INTO halls 
                    (id, name, description, location, size, art_period, exhibit_count) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    [(h["id"], h["name"], h["description"], h["location"], h["size"], 
                      h["art_period"], h["exhibit_count"]) for h in halls_data]
                )
                logger.info(f"Успешно загружено {len(halls_data)} залов")
                
                # Загружаем данные об экспонатах
                exhibits_data = self._load_exhibits_data()
                cursor.executemany(
                    '''INSERT INTO exhibits 
                    (id, hall_id, title, artist, description, art_style, creation_year, 
                     medium, origin_country, tags, multimedia_link) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    [(e["id"], e["hall_id"], e["title"], e["artist"], e["description"], 
                      e["art_style"], e["creation_year"], e["medium"], e["origin_country"], 
                      e["tags"], e["multimedia_link"]) for e in exhibits_data]
                )
                logger.info(f"Успешно загружено {len(exhibits_data)} экспонатов")
                
                # Загружаем данные для museum_knowledge
                knowledge_data = self._load_knowledge_data()
                cursor.executemany(
                    '''INSERT INTO museum_knowledge 
                    (id, category, question, answer, keywords) 
                    VALUES (?, ?, ?, ?, ?)''',
                    [(k["id"], k["category"], k["question"], k["answer"], k["keywords"]) 
                     for k in knowledge_data]
                )
                logger.info(f"Успешно загружено {len(knowledge_data)} записей в museum_knowledge")
                
                # Загружаем данные для routes
                routes_data = self._load_routes_data()
                cursor.executemany(
                    '''INSERT INTO routes 
                    (from_node, to_node, distance) 
                    VALUES (?, ?, ?)''',
                    [(r["from_node"], r["to_node"], r["distance"]) for r in routes_data]
                )
                logger.info(f"Успешно загружено {len(routes_data)} маршрутов")
                
                # Загружаем данные для feedback
                feedback_data = self._load_feedback_data()
                cursor.executemany(
                    '''INSERT INTO feedback 
                    (user_id, rating, feedback, timestamp) 
                    VALUES (?, ?, ?, ?)''',
                    [(f["user_id"], f["rating"], f["feedback"], f["timestamp"]) 
                     for f in feedback_data]
                )
                logger.info(f"Успешно загружено {len(feedback_data)} отзывов")
                
                # Загружаем данные для bookings
                bookings_data = self._load_bookings_data()
                cursor.executemany(
                    '''INSERT INTO bookings 
                    (user_id, time_slot, date, timestamp) 
                    VALUES (?, ?, ?, ?)''',
                    [(b["user_id"], b["time_slot"], b["date"], b["timestamp"]) 
                     for b in bookings_data]
                )
                logger.info(f"Успешно загружено {len(bookings_data)} бронирований")
                
                conn.commit()


        except sqlite3.Error as e:
            logger.error(f"Ошибка при загрузке данных: {e}")
            raise

if __name__ == "__main__":
    # При запуске файла напрямую инициализируем базу данных
    loader = DataLoader()
    loader.initialize_database()
    print("База данных успешно инициализирована с начальными данными")