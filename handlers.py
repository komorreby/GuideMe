from aiogram import types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database import museum_database
from ai_assistant import get_ai_response
from image_recognition import ImageRecognizer
import aiofiles
import os
from loguru import logger
from typing import List, Dict  # Добавляем импорт List и Dict

class UserState(StatesGroup):
    main_menu = State()
    exploring_halls = State()
    exploring_exhibits = State()
    searching = State()
    asking_question = State()
    route_navigation = State()

def setup(dp):
    """Настройка обработчиков для бота с улучшенным UX."""
    recognizer = ImageRecognizer()

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

    def get_hall_navigation(halls: List[Dict]):
        """Динамическая генерация клавиатуры для залов."""
        buttons = [
            InlineKeyboardButton(text=hall["name"], callback_data=f"hall_{hall['id']}")
            for hall in halls
        ]
        # Разбиваем кнопки на строки по 3
        inline_kb = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
        inline_kb.append([
            InlineKeyboardButton(text="Далее ➡️", callback_data="next_hall"),
            InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")
        ])
        return InlineKeyboardMarkup(inline_keyboard=inline_kb)

    @dp.message(Command("start"))
    async def send_welcome(message: types.Message, state: FSMContext):
        welcome_text = (
            "🎨 Добро пожаловать в музей искусств! Я ваш виртуальный гид. "
            "Выберите, что хотите узнать, или просто спросите меня!"
        )
        await message.reply(welcome_text, reply_markup=get_main_menu())
        await state.set_state(UserState.main_menu)

    @dp.message(lambda message: message.text == "🏛️ Залы", UserState.main_menu)
    async def start_halls_exploration(message: types.Message, state: FSMContext):
        halls = museum_database.get_all_halls()
        await message.reply("Выберите зал для исследования:", reply_markup=get_hall_navigation(halls))
        await state.set_state(UserState.exploring_halls)
        await state.update_data(hall_index=0, halls=halls)

    @dp.callback_query(lambda c: c.data.startswith("hall_"), UserState.exploring_halls)
    async def show_hall_details(callback: types.CallbackQuery, state: FSMContext):
        hall_id = int(callback.data.split("_")[1])
        hall = museum_database.get_hall_info(hall_id)
        if hall:
            response = f"*{hall['name']}*\n{hall['description']}\n📍 {hall['location']}\nПериод: {hall['art_period']}\nЭкспонатов: {hall['exhibit_count']}"
            halls = museum_database.get_all_halls()
            await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=get_hall_navigation(halls))
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "next_hall", UserState.exploring_halls)
    async def next_hall(callback: types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        hall_index = data.get("hall_index", 0) + 1
        halls = data.get("halls", museum_database.get_all_halls())
        if hall_index < len(halls):
            hall = halls[hall_index]
            response = f"*{hall['name']}*\n{hall['description']}\n📍 {hall['location']}\nПериод: {hall['art_period']}\nЭкспонатов: {hall['exhibit_count']}"
            await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=get_hall_navigation(halls))
            await state.update_data(hall_index=hall_index)
        else:
            await callback.message.edit_text("Все залы просмотрены!", reply_markup=get_hall_navigation(halls))
        await callback.answer()

    @dp.message(lambda message: message.text == "🖼️ Экспонаты", UserState.main_menu)
    async def start_exhibits_exploration(message: types.Message, state: FSMContext):
        exhibits = museum_database.get_all_exhibits()
        await state.update_data(exhibits=exhibits, exhibit_index=0)
        await show_next_exhibit(message, state)
        await state.set_state(UserState.exploring_exhibits)

    async def show_next_exhibit(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        exhibits = data["exhibits"]
        index = data.get("exhibit_index", 0)
        if index < len(exhibits):
            ex = exhibits[index]
            response = f"*{ex['title']}*\nАвтор: {ex['artist']}\n{ex['description']}\nСтиль: {ex['art_style']}\nГод: {ex['creation_year']}"
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
        response = "❓ FAQ:\n\n" + "\n".join(f"❔ {q}\n💡 {a}" for q, a in faqs[:10])  # Ограничение до 10
        if len(faqs) > 10:
            response += "\n\nИ ещё больше ответов доступно у AI-ассистента!"
        await message.reply(response, reply_markup=get_main_menu())

    @dp.message(lambda message: message.text == "🔍 Поиск", UserState.main_menu)
    async def start_search(message: types.Message, state: FSMContext):
        await message.reply("Назови произведение, художника или стиль!")
        await state.set_state(UserState.searching)

    @dp.message(UserState.searching)
    async def process_search(message: types.Message, state: FSMContext):
        results = museum_database.search_exhibits(message.text)
        response = "🔍 Результаты:\n\n" + (
            "\n".join(f"*{ex['title']}* ({ex['artist']})\n{ex['description']}" for ex in results) if results else "Ничего не найдено."
        )
        await message.reply(response, parse_mode="Markdown", reply_markup=get_main_menu())
        await state.set_state(UserState.main_menu)

    @dp.message(lambda message: message.text == "🌍 Маршрут", UserState.main_menu)
    async def start_route(message: types.Message, state: FSMContext):
        halls = museum_database.get_all_halls()
        steps = [f"{i+1}. {hall['name']}: {hall['description'].split('.')[0]}." for i, hall in enumerate(halls)]
        steps.append(f"{len(halls)+1}. Выход: завершите тур у сувенирного магазина.")
        await state.update_data(route_steps=steps, route_step=0)
        await show_route_step(message, state)
        await state.set_state(UserState.route_navigation)

    async def show_route_step(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
        data = await state.get_data()
        steps = data["route_steps"]
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
        steps = data["route_steps"]
        step = data.get("route_step", 0)
        if callback.data == "next_step":
            step = min(step + 1, len(steps) - 1)
        else:
            step = max(0, step - 1)
        await state.update_data(route_step=step)
        await show_route_step(callback, state)
        await callback.answer()

    @dp.message(lambda message: message.text == "💬 Вопрос AI", UserState.main_menu)
    async def start_asking(message: types.Message, state: FSMContext):
        await message.reply("Спроси меня об искусстве или пришли фото картины для распознавания!")
        await state.set_state(UserState.asking_question)

    @dp.message(UserState.asking_question)
    async def handle_question_or_photo(message: types.Message, state: FSMContext):
        if message.photo:
            logger.info(f"Получено фото от пользователя {message.from_user.id}")
            photo = message.photo[-1]
            file_path = f"temp_{photo.file_id}.jpg"
            try:
                file = await message.bot.get_file(photo.file_id)
                await message.bot.download_file(file.file_path, file_path)
                recognized_objects = recognizer.recognize_image(file_path)
                matches = recognizer.match_with_exhibits(recognized_objects)

                if matches:
                    response = "🔍 Найдены связанные экспонаты:\n\n"
                    for obj, exhibit in matches:
                        response += (
                            f"*{exhibit['title']}*\n"
                            f"Объект: {obj['class']} (Уверенность: {obj['confidence']:.2%})\n"
                            f"Автор: {exhibit['artist']}\n"
                            f"Описание: {exhibit['description']}\n\n"
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