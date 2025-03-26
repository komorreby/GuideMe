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
            # Оптимизированный промпт с использованием f-строки и минимальной длины
            prompt = (
                f"Ты - виртуальный экскурсовод музея искусств, тебя зовут Гылыков Гэсэр, эксперт с глубокими знаниями истории искусства, стилей и художников. "
                f"Отвечай только на вопросы, связанные с искусством, музеем, его коллекциями, художниками или историческим контекстом экспонатов. "
                f"Если вопрос выходит за рамки темы, вежливо перенаправь пользователя к искусству. "
                f"Ограничь ответ 500 символами, но делай его максимально содержательным, избегая лишних слов. "
                f"Адаптируй стиль ответа под уровень вопроса: от простого и увлекательного для новичков до детального и академичного для знатоков. "
                f"Переведи ответ на язык вопроса, сохраняя культурную тонкость перевода. "
                f"Добавь любопытный факт или связь с экспонатом, если это уместно. "
                f"Контекст: {context or 'Нет доступного контекста — используй общие знания об искусстве'}\n\n"
                f"Вопрос: {query}"
            )
            response = self.giga_client.chat(prompt).choices[0].message.content
            # Обрезаем ответ до 500 символов, если он превышает
            return response[:500]
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return "Извините, попробуйте перефразировать вопрос."

class ContextManager:
    def get_relevant_context(self, query: str) -> str:
        """Получение релевантного контекста из базы данных."""
        # Поиск в FAQ (оптимизация: регистронезависимый поиск сразу в базе)
        faqs = museum_database.get_faq()
        for question, answer in faqs:
            if query.lower() in question.lower():
                return answer

        # Поиск в экспонатах
        exhibits = museum_database.search_exhibits(query)
        if exhibits:
            return " ".join(f"{ex[2]}: {ex[3]}" for ex in exhibits)
        return "Нет специфического контекста"

# Глобальный экземпляр ассистента (ленивая инициализация не требуется)
museum_ai_assistant = MuseumAIAssistant()

def get_ai_response(user_input: str) -> str:
    """Интерфейс для получения ответа от AI-ассистента."""
    return museum_ai_assistant.generate_response(user_input)