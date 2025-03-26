import sqlite3
import csv
from typing import List, Tuple, Optional, Dict
from contextlib import contextmanager
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MuseumDatabase:
    def __init__(self, db_path: str = "art_museum.db", timeout: float = 5.0, data_dir: str = "data"):
        """
        Инициализация базы данных музея искусств.
        
        Args:
            db_path (str): Путь к файлу базы данных
            timeout (float): Таймаут соединения в секундах
            data_dir (str): Папка с CSV-файлами данных
        """
        self.db_path = db_path
        self.timeout = timeout
        self.data_dir = data_dir
        # Создаём папку data, если её нет
        os.makedirs(self.data_dir, exist_ok=True)
        self._initialize_database()

    @contextmanager
    def _get_connection(self):
        """Контекстный менеджер для управления соединением с БД."""
        conn = sqlite3.connect(self.db_path, timeout=self.timeout)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Ошибка базы данных: {e}")
            raise
        finally:
            conn.close()

    def _initialize_database(self):
        """Инициализация структуры базы данных и загрузка данных."""
        try:
            with self._get_connection() as conn:
                self._create_tables(conn)
                self._load_or_export_data(conn)
        except sqlite3.Error as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise

    def _create_tables(self, conn: sqlite3.Connection):
        """Создание таблиц базы данных с индексами для оптимизации поиска."""
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS halls (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                location TEXT,
                size INTEGER,
                art_period TEXT,
                exhibit_count INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_halls_art_period ON halls(art_period);

            CREATE TABLE IF NOT EXISTS exhibits (
                id INTEGER PRIMARY KEY,
                hall_id INTEGER,
                title TEXT NOT NULL,
                artist TEXT,
                description TEXT,
                art_style TEXT,
                creation_year INTEGER,
                medium TEXT,
                origin_country TEXT,
                tags TEXT,
                multimedia_link TEXT,
                FOREIGN KEY(hall_id) REFERENCES halls(id)
            );
            CREATE INDEX IF NOT EXISTS idx_exhibits_title ON exhibits(title);
            CREATE INDEX IF NOT EXISTS idx_exhibits_artist ON exhibits(artist);
            CREATE INDEX IF NOT EXISTS idx_exhibits_tags ON exhibits(tags);

            CREATE TABLE IF NOT EXISTS museum_knowledge (
                id INTEGER PRIMARY KEY,
                category TEXT,
                question TEXT,
                answer TEXT,
                keywords TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_knowledge_keywords ON museum_knowledge(keywords);

            CREATE TABLE IF NOT EXISTS routes (
                from_node TEXT,
                to_node TEXT,
                distance REAL,
                FOREIGN KEY (from_node) REFERENCES halls(id),
                FOREIGN KEY (to_node) REFERENCES halls(id)
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                feedback TEXT,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                time_slot TEXT NOT NULL,
                date TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
        ''')
        conn.commit()

    def _load_or_export_data(self, conn: sqlite3.Connection):
        """Загрузка данных из CSV или экспорт из базы, если CSV нет."""
        csv_files = {
            "halls": "halls.csv",
            "exhibits": "exhibits.csv",
            "museum_knowledge": "museum_knowledge.csv",
            "routes": "routes.csv"
        }
        
        # Проверяем наличие CSV-файлов
        all_csv_exist = all(os.path.exists(os.path.join(self.data_dir, filename)) for filename in csv_files.values())
        
        if all_csv_exist:
            # Если все CSV есть, загружаем данные из них
            for table, filename in csv_files.items():
                file_path = os.path.join(self.data_dir, filename)
                self.load_from_csv(table, file_path)
        else:
            # Если хотя бы одного CSV нет, экспортируем данные из базы
            self._export_to_csv()

    def load_from_csv(self, table_name: str, csv_path: str) -> int:
        """Загрузка данных из CSV в указанную таблицу."""
        queries = {
            "halls": "INSERT OR REPLACE INTO halls VALUES (?, ?, ?, ?, ?, ?, ?)",
            "exhibits": "INSERT OR REPLACE INTO exhibits VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            "museum_knowledge": "INSERT OR REPLACE INTO museum_knowledge VALUES (?, ?, ?, ?, ?)",
            "routes": "INSERT OR REPLACE INTO routes VALUES (?, ?, ?)"
        }
        
        if table_name not in queries:
            raise ValueError(f"Неизвестная таблица: {table_name}")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                with open(csv_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)  # Пропускаем заголовок
                    rows = [tuple(row) for row in reader]
                    cursor.executemany(queries[table_name], rows)
                    conn.commit()
                    logger.info(f"Загружено {len(rows)} записей в таблицу {table_name} из {csv_path}")
                    return len(rows)
        except (sqlite3.Error, csv.Error) as e:
            logger.error(f"Ошибка загрузки CSV: {e}")
            raise

    def _export_to_csv(self):
        """Экспорт данных из таблиц SQLite в CSV-файлы."""
        tables = {
            "halls": ["id", "name", "description", "location", "size", "art_period", "exhibit_count"],
            "exhibits": ["id", "hall_id", "title", "artist", "description", "art_style", "creation_year", "medium", "origin_country", "tags", "multimedia_link"],
            "museum_knowledge": ["id", "category", "question", "answer", "keywords"],
            "routes": ["from_node", "to_node", "distance"]
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for table, columns in tables.items():
                file_path = os.path.join(self.data_dir, f"{table}.csv")
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                
                # Если таблица пуста, записываем только заголовки
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(columns)  # Записываем заголовки
                    if rows:
                        for row in rows:
                            writer.writerow([row[col] for col in columns])
                    logger.info(f"Экспортировано {len(rows)} записей из таблицы {table} в {file_path}")

    def get_hall_info(self, hall_id: int) -> Optional[Dict]:
        """Получение информации о зале по ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM halls WHERE id = ?", (hall_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    def get_exhibit_info(self, exhibit_id: int) -> Optional[Dict]:
        """Получение информации об экспонате по ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibits WHERE id = ?", (exhibit_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    def search_exhibits(self, keywords: str, limit: int = 10) -> List[Dict]:
        """Поиск экспонатов по ключевым словам с лимитом результатов."""
        query = """
            SELECT * FROM exhibits 
            WHERE tags LIKE ? OR title LIKE ? OR artist LIKE ? OR description LIKE ?
            LIMIT ?
        """
        params = (f"%{keywords}%", f"%{keywords}%", f"%{keywords}%", f"%{keywords}%", limit)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_faq(self, category: str = None) -> List[Tuple[str, str]]:
        """Получение FAQ по категории или всех записей."""
        query = "SELECT question, answer FROM museum_knowledge"
        params = ()
        if category:
            query += " WHERE category = ?"
            params = (category,)
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_exhibits_by_hall(self, hall_id: int) -> List[Dict]:
        """Получение всех экспонатов в указанном зале."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibits WHERE hall_id = ?", (hall_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_halls(self) -> List[Dict]:
        """Получение всех залов."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM halls ORDER BY id")
            return [dict(row) for row in cursor.fetchall()]

    def get_all_exhibits(self) -> List[Dict]:
        """Получение всех экспонатов."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibits ORDER BY id")
            return [dict(row) for row in cursor.fetchall()]

    def find_route(self, from_hall_id: int, to_hall_id: int) -> str:
        """Поиск маршрута между залами с использованием алгоритма Дейкстры."""
        # Получаем все маршруты из таблицы routes
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT from_node, to_node, distance FROM routes")
            routes = cursor.fetchall()

        # Создаём граф (неориентированный)
        graph = {}
        for from_node, to_node, distance in routes:
            if from_node not in graph:
                graph[from_node] = {}
            if to_node not in graph:
                graph[to_node] = {}
            # Добавляем двусторонние связи
            graph[from_node][to_node] = float(distance)
            graph[to_node][from_node] = float(distance)  # Обратная связь

        # Проверяем, существуют ли начальный и конечный залы в графе
        from_hall_str = str(from_hall_id)
        to_hall_str = str(to_hall_id)
        if from_hall_str not in graph:
            return f"Зал с ID {from_hall_id} не найден в маршрутах."
        if to_hall_str not in graph:
            return f"Зал с ID {to_hall_id} не найден в маршрутах."

        # Алгоритм Дейкстры
        distances = {node: float('infinity') for node in graph}
        distances[from_hall_str] = 0
        previous = {node: None for node in graph}
        unvisited = set(graph.keys())

        while unvisited:
            current = min(unvisited, key=lambda node: distances[node])
            if current == to_hall_str:
                break
            unvisited.remove(current)

            for neighbor, weight in graph[current].items():
                if neighbor in unvisited:
                    new_distance = distances[current] + weight
                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
                        previous[neighbor] = current

        # Проверяем, найден ли путь
        if distances[to_hall_str] == float('infinity'):
            return "Маршрут не найден. Возможно, залы не связаны."

        # Восстанавливаем путь
        path = []
        current = to_hall_str
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()

        # Формируем описание маршрута
        halls = self.get_all_halls()
        hall_dict = {str(hall['id']): hall['name'] for hall in halls}
        route_description = "Ваш маршрут:\n"
        for i in range(len(path) - 1):
            from_hall = hall_dict[path[i]]
            to_hall = hall_dict[path[i + 1]]
            route_description += f"Пройдите из '{from_hall}' в '{to_hall}'.\n"
        return route_description

    def save_feedback(self, user_id: int, rating: int, feedback: str, timestamp: str) -> None:
        """Сохранение отзыва в базе данных."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO feedback (user_id, rating, feedback, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (user_id, rating, feedback, timestamp))
            conn.commit()
            logger.info(f"Отзыв сохранён: user_id={user_id}, rating={rating}, timestamp={timestamp}")

    def save_booking(self, user_id: int, time_slot: str, date: str, timestamp: str) -> None:
        """Сохранение записи на экскурсию в базе данных."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bookings (user_id, time_slot, date, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (user_id, time_slot, date, timestamp))
            conn.commit()
            logger.info(f"Запись на экскурсию сохранена: user_id={user_id}, time_slot={time_slot}, date={date}")

    def __del__(self):
        """Деструктор для гарантированного закрытия соединения."""
        logger.debug("Закрытие соединения с базой данных")

museum_database = MuseumDatabase()