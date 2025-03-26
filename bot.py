import asyncio
from aiogram import Bot, Dispatcher
import handlers
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Токен бота (рекомендуется вынести в переменные окружения)
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Подключение обработчиков
handlers.setup(dp)

async def main():
    """Запуск бота с выводом статуса."""
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())