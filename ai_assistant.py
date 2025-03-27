import logging
import sys
import base64
from gigachat import GigaChat
from typing import List, Dict
from database import museum_database

# Настройка логирования для отслеживания работы программы
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Константы для GigaChat (рекомендуется вынести в конфигурационный файл или переменные окружения)
GIGACHAT_CLIENT_ID = "34c24375-4188-4734-bd7c-419da40d06f6"
GIGACHAT_CLIENT_SECRET = "0687d1ee-32f6-4a1a-ae6c-90a56a501494"
CREDENTIALS = base64.b64encode(f"{GIGACHAT_CLIENT_ID}:{GIGACHAT_CLIENT_SECRET}".encode('utf-8')).decode('utf-8')

class MuseumAIAssistant:
    def __init__(self):
        """Инициализация AI-ассистента музея."""
        self.giga_client = self._initialize_gigachat()
        self.context_manager = ContextManager()

    def _initialize_gigachat(self) -> GigaChat:
        """Инициализация клиента GigaChat с обработкой ошибок."""
        try:
            return GigaChat(
                credentials=CREDENTIALS,
                scope="GIGACHAT_API_PERS",
                model="GigaChat-Pro",
                ca_bundle_file="russian_trusted_root_ca.cer",
                verify_ssl_certs=True
            )
        except Exception as e:
            logger.error(f"Ошибка инициализации GigaChat: {e}")
            raise

    def generate_response(self, query: str) -> str:
        """
        Генерация ответа на основе запроса с использованием контекста.
        Ограничение ответа: 500 символов.
        """
        try:
            context = self.context_manager.get_relevant_context(query)
            prompt = (
                f"Ты - виртуальный экскурсовод музея искусств, GuideMe, эксперт в истории искусства. "
                f"Отвечай только на вопросы об искусстве, музее, экспонатах, художниках или истории. "
                f"Если вопрос не в теме, перенаправь к искусству. Ограничь ответ 1000 символами. "
                f"Адаптируй стиль под уровень вопроса: простой для новичков, академичный для знатоков. "
                f"Переведи ответ на язык вопроса. Добавь факт, если уместно. "
                f"Контекст: {context}\n\n"
                f"Вопрос: {query}"
            )
            response = self.giga_client.chat(prompt).choices[0].message.content
            return response[:500]
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return "Извините, попробуйте перефразировать вопрос."

class ContextManager:
    def __init__(self):
        """Инициализация менеджера контекста с загрузкой всех данных из базы."""
        self.full_context = self._load_full_context()

    def _load_full_context(self) -> str:
        """Загрузка всей информации из базы данных в строковый контекст."""
        try:
            context_parts = []

            # 1. Данные из museum_knowledge
            knowledge = museum_database.get_faq()  # Предполагается, что get_faq возвращает список кортежей (вопрос, ответ)
            if knowledge:
                knowledge_str = "FAQ музея:\n" + "\n".join(f"Q: {q}\nA: {a}" for q, a in knowledge)
                context_parts.append(knowledge_str)

            # 2. Данные из exhibits
            exhibits = museum_database.get_all_exhibits()  # Предполагаем новый метод для получения всех экспонатов
            if exhibits:
                exhibits_str = "Экспонаты:\n" + "\n".join(
                    f"{ex['title']} ({ex['artist']}, {ex['creation_year']}): {ex['description']} "
                    f"[Зал {ex['hall_id']}, стиль: {ex['art_style']}, теги: {ex['tags']}]"
                    for ex in exhibits
                )
                context_parts.append(exhibits_str)

            # 3. Данные из halls
            halls = museum_database.get_all_halls()  # Предполагаем новый метод для получения всех залов
            if halls:
                halls_str = "Залы:\n" + "\n".join(
                    f"ID {h['id']}: {h['name']} ({h['location']}, {h['art_period']}): {h['description']} "
                    f"[размер: {h['size']} м², экспонатов: {h['exhibit_count']}]"
                    for h in halls
                )
                context_parts.append(halls_str)

            # Объединяем все части контекста
            full_context = "\n\n".join(context_parts)
            logger.info(f"Контекст загружен: {len(full_context)} символов")
            return full_context if full_context else "База данных пуста."

        except Exception as e:
            logger.error(f"Ошибка загрузки контекста: {e}")
            return "Контекст недоступен из-за ошибки в базе данных."

    def get_relevant_context(self, query: str) -> str:
        """
        Возвращает релевантный контекст на основе запроса.
        Если запрос конкретный, фильтрует контекст, иначе возвращает всё.
        """
        query_lower = query.lower()
        
        # Проверяем, есть ли точное совпадение в FAQ
        for question, answer in museum_database.get_faq():
            if query_lower in question.lower():
                return f"Ответ из FAQ: {answer}"

        # Если запрос связан с конкретным экспонатом, залом или маршрутом, фильтруем
        filtered_context = []
        for line in self.full_context.split("\n"):
            if query_lower in line.lower():
                filtered_context.append(line)
        
        if filtered_context:
            return "\n".join(filtered_context)
        
        # Если нет точных совпадений, возвращаем весь контекст
        return self.full_context

# Глобальный экземпляр ассистента
museum_ai_assistant = MuseumAIAssistant()

def get_ai_response(user_input: str) -> str:
    """Интерфейс для получения ответа от AI-ассистента."""
    return museum_ai_assistant.generate_response(user_input)