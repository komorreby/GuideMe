from aiogram import types
from aiogram.filters import Command  # Оставляем только Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database import museum_database
from ai_assistant import get_ai_response
from image_recognition import ImageRecognizer
import aiofiles
import os
from loguru import logger

# Определяем состояния для управления диалогом
class UserState(StatesGroup):
    main_menu = State()
    exploring_halls = State()
    exploring_exhibits = State()
    searching = State()
    asking_question = State()
    route_navigation = State()

def setup(dp):
    """Настройка обработчиков для бота с улучшенным UX."""
    recognizer = ImageRecognizer()  # Инициализируем распознаватель

    # Основное меню (реплай-клавиатура)
    def get_main_menu():
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🏛️ Залы"), KeyboardButton(text="🖼️ Экспонаты")],
                [KeyboardButton(text="❓ FAQ"), KeyboardButton(text="🔍 Поиск")],
                [KeyboardButton(text="🌍 Маршрут"), KeyboardButton(text="💬 Вопрос AI")],
                [KeyboardButton(text="🔙 В начало")]
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )

    # Инлайн-клавиатура для навигации по залам
    def get_hall_navigation():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Ренессанс", callback_data="hall_1"),
             InlineKeyboardButton(text="Модернизм", callback_data="hall_2")],
            [InlineKeyboardButton(text="Восточное искусство", callback_data="hall_3"),
             InlineKeyboardButton(text="Далее ➡️", callback_data="next_hall")],
            [InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")]
        ])

    @dp.message(Command("start"))
    async def send_welcome(message: types.Message, state: FSMContext):
        """Приветствие с установкой начального состояния."""
        welcome_text = (
            "🎨 Добро пожаловать в музей искусств! Я ваш виртуальный гид. "
            "Выберите, что хотите узнать, или просто спросите меня!"
        )
        await message.reply(welcome_text, reply_markup=get_main_menu())
        await state.set_state(UserState.main_menu)

    @dp.message(lambda message: message.text == "🏛️ Залы", UserState.main_menu)
    async def start_halls_exploration(message: types.Message, state: FSMContext):
        await message.reply("Выберите зал для исследования:", reply_markup=get_hall_navigation())
        await state.set_state(UserState.exploring_halls)
        await state.update_data(hall_index=0)

    @dp.callback_query(lambda c: c.data.startswith("hall_"), UserState.exploring_halls)
    async def show_hall_details(callback: types.CallbackQuery, state: FSMContext):
        hall_id = int(callback.data.split("_")[1])
        hall = museum_database.get_hall_info(hall_id)
        if hall:
            response = f"*{hall[1]}*\n{hall[2]}\n📍 {hall[3]}\nПериод: {hall[5]}"
            await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=get_hall_navigation())
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "next_hall", UserState.exploring_halls)
    async def next_hall(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        hall_index = data.get("hall_index", 0) + 1
        hall_ids = [1, 2, 3]
        if hall_index < len(hall_ids):
            hall = museum_database.get_hall_info(hall_ids[hall_index])
            response = f"*{hall[1]}*\n{hall[2]}\n📍 {hall[3]}\nПериод: {hall[5]}"
            await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=get_hall_navigation())
            await state.update_data(hall_index=hall_index)
        else:
            await callback.message.edit_text("Все залы просмотрены!", reply_markup=get_hall_navigation())
        await callback.answer()

    @dp.message(lambda message: message.text == "🖼️ Экспонаты", UserState.main_menu)
    async def start_exhibits_exploration(message: types.Message, state: FSMContext):
        exhibits = [museum_database.get_exhibit_info(i) for i in range(1, 6)]
        await state.update_data(exhibits=exhibits, exhibit_index=0)
        await show_next_exhibit(message, state)
        await state.set_state(UserState.exploring_exhibits)

    async def show_next_exhibit(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        exhibits = data["exhibits"]
        index = data.get("exhibit_index", 0)
        if index < len(exhibits):
            ex = exhibits[index]
            response = f"*{ex[2]}*\nАвтор: {ex[3]}\n{ex[4]}\nСтиль: {ex[5]}\nГод: {ex[6]}"
            inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Далее ➡️", callback_data="next_exhibit"),
                 InlineKeyboardButton(text="Назад ⬅️", callback_data="prev_exhibit")],
                [InlineKeyboardButton(text="В меню", callback_data="back_to_menu")]
            ])
            if isinstance(message_or_callback, types.Message):
                await message_or_callback.reply(response, parse_mode="Markdown", reply_markup=inline_kb)
            else:
                await message_or_callback.message.edit_text(response, parse_mode="Markdown", reply_markup=inline_kb)

    @dp.callback_query(lambda c: c.data in ["next_exhibit", "prev_exhibit"], UserState.exploring_exhibits)
    async def navigate_exhibits(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        index = data.get("exhibit_index", 0)
        if callback.data == "next_exhibit":
            index += 1
        else:
            index = max(0, index - 1)
        await state.update_data(exhibit_index=index)
        await show_next_exhibit(callback, state)
        await callback.answer()

    @dp.message(lambda message: message.text == "❓ FAQ", UserState.main_menu)
    async def show_faq(message: types.Message):
        faqs = museum_database.get_faq()
        response = "❓ FAQ:\n\n" + "\n".join(f"❔ {q}\n💡 {a}" for q, a in faqs)
        await message.reply(response, reply_markup=get_main_menu())

    @dp.message(lambda message: message.text == "🔍 Поиск", UserState.main_menu)
    async def start_search(message: types.Message, state: FSMContext):
        await message.reply("Назови произведение, художника или стиль!")
        await state.set_state(UserState.searching)

    @dp.message(UserState.searching)
    async def process_search(message: types.Message, state: FSMContext):
        results = museum_database.search_exhibits(message.text)
        response = "🔍 Результаты:\n\n" + (
            "\n".join(f"*{ex[2]}* ({ex[3]})\n{ex[4]}" for ex in results) if results else "Ничего не найдено."
        )
        await message.reply(response, parse_mode="Markdown", reply_markup=get_main_menu())
        await state.set_state(UserState.main_menu)

    @dp.message(lambda message: message.text == "🌍 Помоги с путем", UserState.main_menu)
    async def start_route(message: types.Message, state: FSMContext):
        await state.update_data(route_step=0)
        await show_route_step(message, state)
        await state.set_state(UserState.route_navigation)

    async def show_route_step(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
        steps = [
            "1. Зал Ренессанса: начните с шедевров Возрождения.",
            "2. Зал Модернизма: погрузитесь в искусство XX века.",
            "3. Зал Восточного искусства: откройте азиатскую коллекцию.",
            "4. Выход: завершите тур у сувенирного магазина."
        ]
        data = await state.get_data()
        step = data.get("route_step", 0)
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее ➡️", callback_data="next_step"),
             InlineKeyboardButton(text="Назад ⬅️", callback_data="prev_step")],
            [InlineKeyboardButton(text="В меню", callback_data="back_to_menu")]
        ])
        response = f"🗺️ Маршрут:\n{steps[step]}"
        if isinstance(message_or_callback, types.Message):
            await message_or_callback.reply(response, reply_markup=inline_kb)
        else:
            await message_or_callback.message.edit_text(response, reply_markup=inline_kb)

    @dp.callback_query(lambda c: c.data in ["next_step", "prev_step"], UserState.route_navigation)
    async def navigate_route(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        step = data.get("route_step", 0)
        if callback.data == "next_step":
            step = min(step + 1, 3)
        else:
            step = max(0, step - 1)
        await state.update_data(route_step=step)
        await show_route_step(callback, state)
        await callback.answer()

    @dp.message(lambda message: message.text == "💬 Вопрос AI", UserState.main_menu)
    async def start_asking(message: types.Message, state: FSMContext):
        await message.reply("Спроси меня об искусстве или пришли фото картины для распознавания!")
        await state.set_state(UserState.asking_question)

    @dp.message(UserState.asking_question)  # Единый обработчик для текста и фото
    async def handle_question_or_photo(message: types.Message, state: FSMContext):
        # Проверяем, есть ли фото в сообщении
        if message.photo:
            logger.info(f"Получено фото от пользователя {message.from_user.id}")
            photo = message.photo[-1]  # Берем фото максимального размера
            file_path = f"temp_{photo.file_id}.jpg"

            try:
                # Получаем информацию о файле
                file = await message.bot.get_file(photo.file_id)
                # Скачиваем файл
                await message.bot.download_file(file.file_path, file_path)
                logger.debug(f"Фото сохранено как {file_path}")

                recognized_objects = recognizer.recognize_image(file_path)
                matches = recognizer.match_with_exhibits(recognized_objects)

                if matches:
                    response = "🔍 Найдены связанные экспонаты:\n\n"
                    for obj, exhibit in matches:
                        response += (
                            f"*{exhibit[2]}*\n"
                            f"Объект: {obj['class']} (Уверенность: {obj['confidence']:.2%})\n"
                            f"Автор: {exhibit[3]}\n"
                            f"Описание: {exhibit[4]}\n\n"
                        )
                else:
                    response = "😕 На изображении не найдено связей с экспонатами музея.\n" + str(recognized_objects)

                inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Ещё вопрос", callback_data="more_questions"),
                    InlineKeyboardButton(text="В меню", callback_data="back_to_menu")]
                ])
                await message.reply(response, parse_mode="Markdown", reply_markup=inline_kb)
            except Exception as e:
                logger.error(f"Ошибка распознавания: {e}")
                await message.reply(f"Ошибка распознавания: {e}")
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Временный файл {file_path} удалён")
        else:
            # Обработка текстового вопроса
            response = get_ai_response(message.text)
            inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Ещё вопрос", callback_data="more_questions"),
                InlineKeyboardButton(text="В меню", callback_data="back_to_menu")]
            ])
            await message.reply(response, reply_markup=inline_kb)

    @dp.callback_query(lambda c: c.data == "more_questions", UserState.asking_question)
    async def more_questions(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text("Задай ещё один вопрос об искусстве или пришли фото!", reply_markup=None)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "back_to_menu")
    async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
        await callback.message.delete()
        await callback.message.answer("Вы вернулись в главное меню.", reply_markup=get_main_menu())
        await state.set_state(UserState.main_menu)
        await callback.answer()

    @dp.message(lambda message: message.text == "🔙 В начало")
    async def reset_to_menu(message: types.Message, state: FSMContext):
        await message.reply("Вы вернулись в главное меню.", reply_markup=get_main_menu())
        await state.set_state(UserState.main_menu)

    @dp.message()
    async def handle_free_text(message: types.Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state == UserState.main_menu.state:
            text = message.text.lower()
            if "зал" in text:
                await start_halls_exploration(message, state)
            elif "экспонат" in text or "картин" in text:
                await start_exhibits_exploration(message, state)
            elif "поиск" in text:
                await start_search(message, state)
            elif "маршрут" in text:
                await start_route(message, state)
            elif "вопрос" in text or "?" in text:
                await start_asking(message, state)
            else:
                await message.reply("Не понял, выбери из меню или уточни!", reply_markup=get_main_menu())