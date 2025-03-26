from aiogram import types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database import museum_database
from ai_assistant import get_ai_response
from image_recognition import ImageRecognizer
from gtts import gTTS
import aiofiles
import os
import re
from loguru import logger
from typing import List, Dict
from datetime import datetime

# Определяем состояния для управления диалогом
class UserState(StatesGroup):
    main_menu = State()
    exploring_halls = State()
    exploring_exhibits = State()
    asking_question = State()
    route_navigation = State()
    hall_to_hall_navigation = State()
    selecting_from_hall = State()
    selecting_to_hall = State()
    leaving_feedback = State()
    selecting_rating = State()
    booking_tour = State()

def remove_emoji(text: str) -> str:
    """Удаляет эмодзи из текста."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002700-\U000027BF"
        "\U00002600-\U000026FF"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r"", text).strip()

async def send_voice_message(message_or_callback: types.Message | types.CallbackQuery, text: str, lang: str = "ru"):
    """Генерирует и отправляет голосовое сообщение с заданным текстом, удаляя эмодзи."""
    try:
        clean_text = remove_emoji(text).replace("*", "")
        if not clean_text:
            clean_text = "Текст для озвучивания пуст."

        tts = gTTS(text=clean_text, lang=lang)
        audio_path = "voice_message.mp3"
        tts.save(audio_path)

        with open(audio_path, "rb") as audio_file:
            if isinstance(message_or_callback, types.Message):
                await message_or_callback.reply_voice(
                    voice=types.BufferedInputFile(audio_file.read(), filename="voice_message.mp3")
                )
            else:
                await message_or_callback.message.reply_voice(
                    voice=types.BufferedInputFile(audio_file.read(), filename="voice_message.mp3")
                )

        os.remove(audio_path)
    except Exception as e:
        error_msg = f"Ошибка при генерации голосового сообщения: {e}"
        if isinstance(message_or_callback, types.Message):
            await message_or_callback.reply(error_msg)
        else:
            await message_or_callback.message.reply(error_msg)

def setup(dp):
    """Настройка обработчиков для бота с улучшенным UX."""
    recognizer = ImageRecognizer()

    # Основное меню (реплай-клавиатура)
    def get_main_menu():
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🏛️ Залы"), KeyboardButton(text="🖼️ Экспонаты")],
                [KeyboardButton(text="❓ FAQ")],
                [KeyboardButton(text="🌍 Маршрут"), KeyboardButton(text="🗺️ Навигация между залами")],
                [KeyboardButton(text="💬 Вопрос AI"), KeyboardButton(text="📝 Оставить отзыв")],
                [KeyboardButton(text="📅 Записаться на экскурсию"), KeyboardButton(text="🔙 В начало")],
            ],
            resize_keyboard=True,
            one_time_keyboard=False
        )

    # Инлайн-клавиатура с навигацией по разделам
    def get_navigation_keyboard(exclude_section: str = None):
        """Генерирует клавиатуру с кнопками перехода между разделами."""
        sections = [
            ("🏛️ Залы", "go_to_halls"),
            ("🖼️ Экспонаты", "go_to_exhibits"),
            ("❓ FAQ", "go_to_faq"),
            ("🌍 Маршрут", "go_to_route"),
            ("🗺️ Навигация", "go_to_hall_to_hall"),
            ("💬 Вопрос AI", "go_to_ask_ai"),
            ("📝 Отзыв", "go_to_feedback"),
            ("📅 Экскурсия", "go_to_book_tour"),
            ("🔙 В начало", "back_to_menu")
        ]
        keyboard = []
        row = []
        for text, callback in sections:
            if exclude_section and callback == exclude_section:
                continue
            row.append(InlineKeyboardButton(text=text, callback_data=callback))
            if len(row) == 3:  # Ограничиваем 3 кнопки в ряду
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    # Инлайн-клавиатура для навигации по залам
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
            InlineKeyboardButton(text="Озвучить", callback_data="voice_hall")
        ])
        navigation = get_navigation_keyboard(exclude_section="go_to_halls")
        inline_kb.extend(navigation.inline_keyboard)
        return InlineKeyboardMarkup(inline_keyboard=inline_kb)

    # Инлайн-клавиатура для выбора зала (для навигации между залами)
    def get_hall_selection_keyboard(prefix: str, halls: List[Dict], exclude_hall_id: int = None, voice_callback: str = None):
        keyboard = []
        for hall in halls:
            if exclude_hall_id and hall["id"] == exclude_hall_id:
                continue
            keyboard.append([InlineKeyboardButton(text=hall["name"], callback_data=f"{prefix}_{hall['id']}")])
        if voice_callback:
            keyboard.append([InlineKeyboardButton(text="Озвучить", callback_data=voice_callback)])
        navigation = get_navigation_keyboard(exclude_section="go_to_hall_to_hall")
        keyboard.extend(navigation.inline_keyboard)
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    # Инлайн-клавиатура для выбора времени экскурсии
    def get_tour_time_keyboard():
        times = [
            ("10:00", "tour_time_10_00"),
            ("12:00", "tour_time_12_00"),
            ("14:00", "tour_time_14_00"),
            ("16:00", "tour_time_16_00")
        ]
        keyboard = []
        for time, callback in times:
            keyboard.append([InlineKeyboardButton(text=time, callback_data=callback)])
        navigation = get_navigation_keyboard(exclude_section="go_to_book_tour")
        keyboard.extend(navigation.inline_keyboard)
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    # Инлайн-клавиатура для выбора рейтинга
    def get_rating_keyboard():
        ratings = [
            ("★☆☆☆☆ (1)", "rating_1"),
            ("★★☆☆☆ (2)", "rating_2"),
            ("★★★☆☆ (3)", "rating_3"),
            ("★★★★☆ (4)", "rating_4"),
            ("★★★★★ (5)", "rating_5")
        ]
        keyboard = []
        for rating, callback in ratings:
            keyboard.append([InlineKeyboardButton(text=rating, callback_data=callback)])
        navigation = get_navigation_keyboard(exclude_section="go_to_feedback")
        keyboard.extend(navigation.inline_keyboard)
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @dp.message(Command("start"))
    async def send_welcome(message: types.Message, state: FSMContext):
        """Приветствие с установкой начального состояния и обработкой QR-кодов."""
        user_id = message.from_user.id
        text = message.text.strip()
        param = None
        if text.startswith("/start "):
            param = text.split(" ", 1)[1]

        if param:
            if param.startswith("hall_"):
                try:
                    hall_id = int(param.split("_")[1])
                    hall = museum_database.get_hall_info(hall_id)
                    if hall:
                        await state.update_data(current_hall_id=hall_id)
                        response = (
                            f"📍 Вы находитесь в: *{hall['name']}*\n"
                            f"{hall['description']}\n"
                            f"Период: {hall['art_period']}\n\n"
                            f"Куда бы вы хотели пойти?"
                        )
                        halls = museum_database.get_all_halls()
                        keyboard = get_hall_selection_keyboard("to_hall", halls, exclude_hall_id=hall_id, voice_callback="voice_to_hall")
                        await state.update_data(current_to_hall_text=response)
                        await message.reply(response, parse_mode="Markdown", reply_markup=keyboard)
                        await state.set_state(UserState.selecting_to_hall)
                        return
                except (IndexError, ValueError):
                    pass

        welcome_text = (
            "🎨 Добро пожаловать в музей искусств! Я ваш виртуальный гид. "
            "Выберите, что хотите узнать, или отсканируйте QR-код, чтобы определить ваше местоположение!"
        )
        await message.reply(welcome_text, reply_markup=get_main_menu())
        await state.set_state(UserState.main_menu)

    @dp.message(lambda message: message.text == "🏛️ Залы", UserState.main_menu)
    async def start_halls_exploration(message: types.Message, state: FSMContext):
        """Запуск исследования залов с инлайн-кнопками."""
        halls = museum_database.get_all_halls()
        await message.reply("Выберите зал для исследования:", reply_markup=get_hall_navigation(halls))
        await state.set_state(UserState.exploring_halls)
        await state.update_data(hall_index=0, halls=halls)

    @dp.callback_query(lambda c: c.data == "go_to_halls")
    async def go_to_halls(callback: types.CallbackQuery, state: FSMContext):
        """Переход в раздел 'Залы'."""
        halls = museum_database.get_all_halls()
        await callback.message.delete()
        await callback.message.answer("Выберите зал для исследования:", reply_markup=get_hall_navigation(halls))
        await state.set_state(UserState.exploring_halls)
        await state.update_data(hall_index=0, halls=halls)
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("hall_"), UserState.exploring_halls)
    async def show_hall_details(callback: types.CallbackQuery, state: FSMContext):
        """Отображение информации о зале по выбору."""
        hall_id = int(callback.data.split("_")[1])
        hall = museum_database.get_hall_info(hall_id)
        if hall:
            response = f"*{hall['name']}*\n{hall['description']}\n📍 {hall['location']}\nПериод: {hall['art_period']}\nЭкспонатов: {hall['exhibit_count']}"
            await state.update_data(current_hall_text=response)
            halls = museum_database.get_all_halls()
            await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=get_hall_navigation(halls))
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "voice_hall", UserState.exploring_halls)
    async def voice_hall_details(callback: types.CallbackQuery, state: FSMContext):
        """Озвучивание информации о текущем зале."""
        data = await state.get_data()
        hall_text = data.get("current_hall_text", "Информация о зале недоступна.")
        await send_voice_message(callback, hall_text)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "next_hall", UserState.exploring_halls)
    async def next_hall(callback: types.CallbackQuery, state: FSMContext):
        """Переход к следующему залу автоматически."""
        data = await state.get_data()
        hall_index = data.get("hall_index", 0) + 1
        halls = data.get("halls", museum_database.get_all_halls())
        if hall_index < len(halls):
            hall = halls[hall_index]
            response = f"*{hall['name']}*\n{hall['description']}\n📍 {hall['location']}\nПериод: {hall['art_period']}\nЭкспонатов: {hall['exhibit_count']}"
            await state.update_data(hall_index=hall_index, current_hall_text=response)
            await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=get_hall_navigation(halls))
        else:
            await callback.message.edit_text("Все залы просмотрены!", reply_markup=get_hall_navigation(halls))
        await callback.answer()

    @dp.message(lambda message: message.text == "🖼️ Экспонаты", UserState.main_menu)
    async def start_exhibits_exploration(message: types.Message, state: FSMContext):
        """Запуск автоматического показа экспонатов."""
        exhibits = museum_database.get_all_exhibits()
        await state.update_data(exhibits=exhibits, exhibit_index=0)
        await show_next_exhibit(message, state)
        await state.set_state(UserState.exploring_exhibits)

    async def show_next_exhibit(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
        """Отображение следующего экспоната с кнопками управления."""
        data = await state.get_data()
        exhibits = data["exhibits"]
        index = data.get("exhibit_index", 0)
        if index < len(exhibits):
            ex = exhibits[index]
            response = f"*{ex['title']}*\nАвтор: {ex['artist']}\n{ex['description']}\nСтиль: {ex['art_style']}\nГод: {ex['creation_year']}"
            inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Далее ➡️", callback_data="next_exhibit"),
                 InlineKeyboardButton(text="Назад ⬅️", callback_data="prev_exhibit")],
                [InlineKeyboardButton(text="Озвучить", callback_data="voice_exhibit")]
            ])
            navigation = get_navigation_keyboard(exclude_section="go_to_exhibits")
            inline_kb.inline_keyboard.extend(navigation.inline_keyboard)
            await state.update_data(current_exhibit_text=response)
            if isinstance(message_or_callback, types.Message):
                await message_or_callback.reply(response, parse_mode="Markdown", reply_markup=inline_kb)
            else:
                await message_or_callback.message.edit_text(response, parse_mode="Markdown", reply_markup=inline_kb)

    @dp.callback_query(lambda c: c.data == "go_to_exhibits")
    async def go_to_exhibits(callback: types.CallbackQuery, state: FSMContext):
        """Переход в раздел 'Экспонаты'."""
        exhibits = museum_database.get_all_exhibits()
        await state.update_data(exhibits=exhibits, exhibit_index=0)
        await callback.message.delete()
        await show_next_exhibit(callback, state)
        await state.set_state(UserState.exploring_exhibits)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "voice_exhibit", UserState.exploring_exhibits)
    async def voice_exhibit_details(callback: types.CallbackQuery, state: FSMContext):
        """Озвучивание информации о текущем экспонате."""
        data = await state.get_data()
        exhibit_text = data.get("current_exhibit_text", "Информация об экспонате недоступна.")
        await send_voice_message(callback, exhibit_text)
        await callback.answer()

    @dp.callback_query(lambda c: c.data in ["next_exhibit", "prev_exhibit"], UserState.exploring_exhibits)
    async def navigate_exhibits(callback: types.CallbackQuery, state: FSMContext):
        """Навигация по экспонатам вперёд и назад."""
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
    async def show_faq(message: types.Message, state: FSMContext):
        """Показ FAQ с возможностью озвучивания."""
        faqs = museum_database.get_faq()
        response = "❓ FAQ:\n\n" + "\n".join(f"❔ {q}\n💡 {a}" for q, a in faqs[:10])
        if len(faqs) > 10:
            response += "\n\nИ ещё больше ответов доступно у AI-ассистента!"
        
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[])
        for idx, (question, answer) in enumerate(faqs[:10]):
            faq_text = f"❔ {question}\n💡 {answer}"
            inline_kb.inline_keyboard.append([
                InlineKeyboardButton(text=f"Озвучить #{idx + 1}", callback_data=f"voice_faq_{idx}")
            ])
        navigation = get_navigation_keyboard(exclude_section="go_to_faq")
        inline_kb.inline_keyboard.extend(navigation.inline_keyboard)

        await state.update_data(faqs=faqs)
        await message.reply(response, reply_markup=inline_kb)

    @dp.callback_query(lambda c: c.data == "go_to_faq")
    async def go_to_faq(callback: types.CallbackQuery, state: FSMContext):
        """Переход в раздел 'FAQ'."""
        faqs = museum_database.get_faq()
        response = "❓ FAQ:\n\n" + "\n".join(f"❔ {q}\n💡 {a}" for q, a in faqs[:10])
        if len(faqs) > 10:
            response += "\n\nИ ещё больше ответов доступно у AI-ассистента!"
        
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[])
        for idx, (question, answer) in enumerate(faqs[:10]):
            faq_text = f"❔ {question}\n💡 {answer}"
            inline_kb.inline_keyboard.append([
                InlineKeyboardButton(text=f"Озвучить #{idx + 1}", callback_data=f"voice_faq_{idx}")
            ])
        navigation = get_navigation_keyboard(exclude_section="go_to_faq")
        inline_kb.inline_keyboard.extend(navigation.inline_keyboard)

        await state.update_data(faqs=faqs)
        await callback.message.delete()
        await callback.message.answer(response, reply_markup=inline_kb)
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("voice_faq_"))
    async def voice_faq(callback: types.CallbackQuery, state: FSMContext):
        """Озвучивание выбранного вопроса и ответа из FAQ."""
        faq_index = int(callback.data.split("_")[-1])
        data = await state.get_data()
        faqs = data.get("faqs", [])
        if faq_index < len(faqs):
            question, answer = faqs[faq_index]
            faq_text = f"Вопрос: {question} Ответ: {answer}"
            await send_voice_message(callback, faq_text)
        else:
            await callback.message.reply("Ошибка: FAQ не найден.")
        await callback.answer()

    @dp.message(lambda message: message.text == "🌍 Маршрут", UserState.main_menu)
    async def start_route(message: types.Message, state: FSMContext):
        """Интерактивный маршрут с пошаговой навигацией."""
        halls = museum_database.get_all_halls()
        steps = [f"{i+1}. {hall['name']}: {hall['description'].split('.')[0]}." for i, hall in enumerate(halls)]
        steps.append(f"{len(halls)+1}. Выход: завершите тур у сувенирного магазина.")
        await state.update_data(route_steps=steps, route_step=0)
        await show_route_step(message, state)
        await state.set_state(UserState.route_navigation)

    @dp.callback_query(lambda c: c.data == "go_to_route")
    async def go_to_route(callback: types.CallbackQuery, state: FSMContext):
        """Переход в раздел 'Маршрут'."""
        halls = museum_database.get_all_halls()
        steps = [f"{i+1}. {hall['name']}: {hall['description'].split('.')[0]}." for i, hall in enumerate(halls)]
        steps.append(f"{len(halls)+1}. Выход: завершите тур у сувенирного магазина.")
        await state.update_data(route_steps=steps, route_step=0)
        await callback.message.delete()
        await show_route_step(callback, state)
        await state.set_state(UserState.route_navigation)
        await callback.answer()

    async def show_route_step(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
        """Отображение шага маршрута."""
        data = await state.get_data()
        steps = data["route_steps"]
        step = data.get("route_step", 0)
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее ➡️", callback_data="next_step"),
             InlineKeyboardButton(text="Назад ⬅️", callback_data="prev_step")]
        ])
        navigation = get_navigation_keyboard(exclude_section="go_to_route")
        inline_kb.inline_keyboard.extend(navigation.inline_keyboard)
        response = f"🗺️ Маршрут:\n{steps[step]}"
        if isinstance(message_or_callback, types.Message):
            await message_or_callback.reply(response, reply_markup=inline_kb)
        else:
            await message_or_callback.message.edit_text(response, reply_markup=inline_kb)

    @dp.callback_query(lambda c: c.data in ["next_step", "prev_step"], UserState.route_navigation)
    async def navigate_route(callback: types.CallbackQuery, state: FSMContext):
        """Навигация по шагам маршрута."""
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

    @dp.message(lambda message: message.text == "🗺️ Навигация между залами", UserState.main_menu)
    async def start_hall_to_hall_navigation(message: types.Message, state: FSMContext):
        """Запуск навигации между залами с учетом текущего местоположения."""
        data = await state.get_data()
        current_hall_id = data.get("current_hall_id")
        halls = museum_database.get_all_halls()
        if current_hall_id:
            hall = museum_database.get_hall_info(current_hall_id)
            response = f"📍 Вы находитесь в: *{hall['name']}*\nКуда бы вы хотели пойти?"
            keyboard = get_hall_selection_keyboard("to_hall", halls, exclude_hall_id=current_hall_id, voice_callback="voice_to_hall")
            await state.update_data(current_to_hall_text=response)
            await message.reply(response, parse_mode="Markdown", reply_markup=keyboard)
            await state.set_state(UserState.selecting_to_hall)
        else:
            response = "📷 Пожалуйста, отсканируйте QR-код, чтобы я знал, где вы находитесь, или выберите зал вручную:"
            await message.reply(response)
            response = "Выберите зал, из которого начинаете:"
            keyboard = get_hall_selection_keyboard("from_hall", halls, voice_callback="voice_from_hall")
            await state.update_data(current_from_hall_text=response)
            await message.reply(response, reply_markup=keyboard)
            await state.set_state(UserState.selecting_from_hall)

    @dp.callback_query(lambda c: c.data == "go_to_hall_to_hall")
    async def go_to_hall_to_hall(callback: types.CallbackQuery, state: FSMContext):
        """Переход в раздел 'Навигация между залами'."""
        data = await state.get_data()
        current_hall_id = data.get("current_hall_id")
        halls = museum_database.get_all_halls()
        await callback.message.delete()
        if current_hall_id:
            hall = museum_database.get_hall_info(current_hall_id)
            response = f"📍 Вы находитесь в: *{hall['name']}*\nКуда бы вы хотели пойти?"
            keyboard = get_hall_selection_keyboard("to_hall", halls, exclude_hall_id=current_hall_id, voice_callback="voice_to_hall")
            await state.update_data(current_to_hall_text=response)
            await callback.message.answer(response, parse_mode="Markdown", reply_markup=keyboard)
            await state.set_state(UserState.selecting_to_hall)
        else:
            response = "📷 Пожалуйста, отсканируйте QR-код, чтобы я знал, где вы находитесь, или выберите зал вручную:"
            await callback.message.answer(response)
            response = "Выберите зал, из которого начинаете:"
            keyboard = get_hall_selection_keyboard("from_hall", halls, voice_callback="voice_from_hall")
            await state.update_data(current_from_hall_text=response)
            await callback.message.answer(response, reply_markup=keyboard)
            await state.set_state(UserState.selecting_from_hall)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "voice_from_hall", UserState.selecting_from_hall)
    async def voice_from_hall(callback: types.CallbackQuery, state: FSMContext):
        """Озвучивание текста выбора начального зала."""
        data = await state.get_data()
        from_hall_text = data.get("current_from_hall_text", "Выберите зал, из которого начинаете.")
        await send_voice_message(callback, from_hall_text)
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("from_hall_"), UserState.selecting_from_hall)
    async def select_from_hall(callback: types.CallbackQuery, state: FSMContext):
        """Выбор начального зала."""
        from_hall_id = int(callback.data.split("_")[-1])
        halls = museum_database.get_all_halls()
        await state.update_data(from_hall_id=from_hall_id, current_hall_id=from_hall_id)
        from_hall = museum_database.get_hall_info(from_hall_id)
        response = f"Вы начинаете из: *{from_hall['name']}*\nВыберите зал, в который хотите попасть:"
        keyboard = get_hall_selection_keyboard("to_hall", halls, exclude_hall_id=from_hall_id, voice_callback="voice_to_hall")
        await state.update_data(current_to_hall_text=response)
        await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=keyboard)
        await state.set_state(UserState.selecting_to_hall)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "voice_to_hall", UserState.selecting_to_hall)
    async def voice_to_hall(callback: types.CallbackQuery, state: FSMContext):
        """Озвучивание текста выбора конечного зала."""
        data = await state.get_data()
        to_hall_text = data.get("current_to_hall_text", "Выберите зал, в который хотите попасть.")
        await send_voice_message(callback, to_hall_text)
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("to_hall_"), UserState.selecting_to_hall)
    async def select_to_hall(callback: types.CallbackQuery, state: FSMContext):
        """Выбор конечного зала и показ маршрута с озвучиванием."""
        to_hall_id = int(callback.data.split("_")[-1])
        data = await state.get_data()
        from_hall_id = data.get("from_hall_id") or data.get("current_hall_id")
        if from_hall_id == to_hall_id:
            halls = museum_database.get_all_halls()
            response = "Вы уже находитесь в этом зале! Выберите другой зал."
            keyboard = get_hall_selection_keyboard("to_hall", halls, exclude_hall_id=from_hall_id, voice_callback="voice_to_hall")
            await state.update_data(current_to_hall_text=response)
            await callback.message.edit_text(response, reply_markup=keyboard)
            await callback.answer()
            return

        from_hall = museum_database.get_hall_info(from_hall_id)
        to_hall = museum_database.get_hall_info(to_hall_id)
        route = museum_database.find_route(from_hall_id, to_hall_id)
        response = f"🗺️ **Маршрут из '{from_hall['name']}' в '{to_hall['name']}':**\n\n{route}"
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Озвучить маршрут", callback_data="voice_route"),
             InlineKeyboardButton(text="Новый маршрут", callback_data="new_hall_to_hall")]
        ])
        navigation = get_navigation_keyboard(exclude_section="go_to_hall_to_hall")
        inline_kb.inline_keyboard.extend(navigation.inline_keyboard)
        await state.update_data(current_route_text=response)
        await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=inline_kb)
        await state.set_state(UserState.hall_to_hall_navigation)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "voice_route", UserState.hall_to_hall_navigation)
    async def voice_route(callback: types.CallbackQuery, state: FSMContext):
        """Озвучивание маршрута."""
        data = await state.get_data()
        route_text = data.get("current_route_text", "Маршрут недоступен.")
        await send_voice_message(callback, route_text)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "new_hall_to_hall", UserState.hall_to_hall_navigation)
    async def new_hall_to_hall_navigation(callback: types.CallbackQuery, state: FSMContext):
        """Запуск нового маршрута между залами."""
        data = await state.get_data()
        current_hall_id = data.get("current_hall_id")
        halls = museum_database.get_all_halls()
        if current_hall_id:
            hall = museum_database.get_hall_info(current_hall_id)
            response = f"📍 Вы находитесь в: *{hall['name']}*\nКуда бы вы хотели пойти?"
            keyboard = get_hall_selection_keyboard("to_hall", halls, exclude_hall_id=current_hall_id, voice_callback="voice_to_hall")
            await state.update_data(current_to_hall_text=response)
            await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=keyboard)
            await state.set_state(UserState.selecting_to_hall)
        else:
            response = "📷 Пожалуйста, отсканируйте QR-код, чтобы я знал, где вы находитесь, или выберите зал вручную:"
            await callback.message.edit_text(response)
            response = "Выберите зал, из которого начинаете:"
            keyboard = get_hall_selection_keyboard("from_hall", halls, voice_callback="voice_from_hall")
            await state.update_data(current_from_hall_text=response)
            await callback.message.edit_text(response, reply_markup=keyboard)
            await state.set_state(UserState.selecting_from_hall)
        await callback.answer()

    @dp.message(lambda message: message.text == "💬 Вопрос AI", UserState.main_menu)
    async def start_asking(message: types.Message, state: FSMContext):
        """Запуск диалога с AI."""
        inline_kb = get_navigation_keyboard(exclude_section="go_to_ask_ai")
        await message.reply("Спроси меня об искусстве, найди экспонат или пришли фото картины для распознавания!", reply_markup=inline_kb)
        await state.set_state(UserState.asking_question)

    @dp.callback_query(lambda c: c.data == "go_to_ask_ai")
    async def go_to_ask_ai(callback: types.CallbackQuery, state: FSMContext):
        """Переход в раздел 'Вопрос AI'."""
        inline_kb = get_navigation_keyboard(exclude_section="go_to_ask_ai")
        await callback.message.delete()
        await callback.message.answer("Спроси меня об искусстве, найди экспонат или пришли фото картины для распознавания!", reply_markup=inline_kb)
        await state.set_state(UserState.asking_question)
        await callback.answer()

    @dp.message(UserState.asking_question)
    async def handle_question_or_photo(message: types.Message, state: FSMContext):
        """Обработка вопроса, фото или поиска с AI."""
        if message.photo:
            logger.info(f"Получено фото от пользователя {message.from_user.id}")
            photo = message.photo[-1]
            file_path = f"temp_{photo.file_id}.jpg"

            try:
                file = await message.bot.get_file(photo.file_id)
                await message.bot.download_file(file.file_path, file_path)
                logger.debug(f"Фото сохранено как {file_path}")

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
                    [InlineKeyboardButton(text="Озвучить ответ", callback_data="voice_ai_response"),
                     InlineKeyboardButton(text="Ещё вопрос", callback_data="more_questions")]
                ])
                navigation = get_navigation_keyboard(exclude_section="go_to_ask_ai")
                inline_kb.inline_keyboard.extend(navigation.inline_keyboard)
                await state.update_data(current_ai_response=response)
                await message.reply(response, parse_mode="Markdown", reply_markup=inline_kb)
            except Exception as e:
                logger.error(f"Ошибка распознавания: {e}")
                await message.reply(f"Ошибка распознавания: {e}")
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Временный файл {file_path} удалён")
        else:
            text = message.text.lower()
            if "маршрут" in text or "путь" in text or "как пройти" in text:
                data = await state.get_data()
                current_hall_id = data.get("current_hall_id")
                halls = museum_database.get_all_halls()
                if current_hall_id:
                    hall = museum_database.get_hall_info(current_hall_id)
                    response = f"📍 Вы находитесь в: *{hall['name']}*\nКуда бы вы хотели пойти?"
                    keyboard = get_hall_selection_keyboard("to_hall", halls, exclude_hall_id=current_hall_id, voice_callback="voice_to_hall")
                    await state.update_data(current_to_hall_text=response)
                    await message.reply(response, parse_mode="Markdown", reply_markup=keyboard)
                    await state.set_state(UserState.selecting_to_hall)
                else:
                    response = "📷 Пожалуйста, отсканируйте QR-код, чтобы я знал, где вы находитесь, или выберите зал вручную:"
                    await message.reply(response)
                    response = "Выберите зал, из которого начинаете:"
                    keyboard = get_hall_selection_keyboard("from_hall", halls, voice_callback="voice_from_hall")
                    await state.update_data(current_from_hall_text=response)
                    await message.reply(response, reply_markup=keyboard)
                    await state.set_state(UserState.selecting_from_hall)
            else:
                # Сначала пытаемся выполнить поиск в базе данных
                results = museum_database.search_exhibits(message.text)
                if results:
                    response = "🔍 Результаты поиска:\n\n" + "\n".join(f"*{ex['title']}* ({ex['artist']})\n{ex['description']}" for ex in results)
                else:
                    # Если ничего не найдено, передаем запрос в GigaChat
                    response = get_ai_response(message.text)
                    if "Ничего не найдено" in response:
                        response = "😕 Ничего не найдено. Попробуйте перефразировать вопрос или уточнить название экспоната."

                inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Озвучить ответ", callback_data="voice_ai_response"),
                     InlineKeyboardButton(text="Ещё вопрос", callback_data="more_questions")]
                ])
                navigation = get_navigation_keyboard(exclude_section="go_to_ask_ai")
                inline_kb.inline_keyboard.extend(navigation.inline_keyboard)
                await state.update_data(current_ai_response=response)
                await message.reply(response, parse_mode="Markdown", reply_markup=inline_kb)

    @dp.callback_query(lambda c: c.data == "voice_ai_response", UserState.asking_question)
    async def voice_ai_response(callback: types.CallbackQuery, state: FSMContext):
        """Озвучивание ответа AI."""
        data = await state.get_data()
        ai_response = data.get("current_ai_response", "Ответ недоступен.")
        await send_voice_message(callback, ai_response)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "more_questions", UserState.asking_question)
    async def more_questions(callback: types.CallbackQuery, state: FSMContext):
        """Продолжение диалога с AI."""
        inline_kb = get_navigation_keyboard(exclude_section="go_to_ask_ai")
        await callback.message.edit_text("Задай ещё один вопрос об искусстве или пришли фото!", reply_markup=inline_kb)
        await callback.answer()

    @dp.message(lambda message: message.text == "📝 Оставить отзыв", UserState.main_menu)
    async def start_leaving_feedback(message: types.Message, state: FSMContext):
        """Запуск процесса оставления отзыва."""
        response = "Пожалуйста, оцените музей от 1 до 5 звезд:"
        inline_kb = get_rating_keyboard()
        await message.reply(response, reply_markup=inline_kb)
        await state.set_state(UserState.selecting_rating)

    @dp.callback_query(lambda c: c.data == "go_to_feedback")
    async def go_to_feedback(callback: types.CallbackQuery, state: FSMContext):
        """Переход в раздел 'Оставить отзыв'."""
        response = "Пожалуйста, оцените музей от 1 до 5 звезд:"
        inline_kb = get_rating_keyboard()
        await callback.message.delete()
        await callback.message.answer(response, reply_markup=inline_kb)
        await state.set_state(UserState.selecting_rating)
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("rating_"), UserState.selecting_rating)
    async def process_rating(callback: types.CallbackQuery, state: FSMContext):
        """Обработка выбора рейтинга."""
        rating = int(callback.data.split("_")[-1])
        await state.update_data(rating=rating)
        response = "Спасибо за вашу оценку! Теперь напишите ваш отзыв о музее:"
        inline_kb = get_navigation_keyboard(exclude_section="go_to_feedback")
        await callback.message.edit_text(response, reply_markup=inline_kb)
        await state.set_state(UserState.leaving_feedback)
        await callback.answer()

    @dp.message(UserState.leaving_feedback)
    async def process_feedback(message: types.Message, state: FSMContext):
        """Сохранение отзыва в базе данных."""
        feedback = message.text
        data = await state.get_data()
        rating = data.get("rating", 0)
        user_id = message.from_user.id
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            museum_database.save_feedback(user_id, rating, feedback, timestamp)
            logger.info(f"Отзыв сохранен в базе данных: user_id={user_id}, rating={rating}, feedback={feedback}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении отзыва в базе данных: {e}")
            await message.reply("Произошла ошибка при сохранении отзыва. Попробуйте снова.")
            return

        response = f"Спасибо за ваш отзыв и оценку ({rating} ★)! 😊 Мы ценим ваше мнение."
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Озвучить подтверждение", callback_data="voice_feedback_confirmation")]
        ])
        navigation = get_navigation_keyboard(exclude_section="go_to_feedback")
        inline_kb.inline_keyboard.extend(navigation.inline_keyboard)
        await state.update_data(feedback_confirmation=response)
        await message.reply(response, reply_markup=inline_kb)
        await state.set_state(UserState.main_menu)

    @dp.callback_query(lambda c: c.data == "voice_feedback_confirmation")
    async def voice_feedback_confirmation(callback: types.CallbackQuery, state: FSMContext):
        """Озвучивание подтверждения отзыва."""
        data = await state.get_data()
        feedback_confirmation = data.get("feedback_confirmation", "Подтверждение недоступно.")
        await send_voice_message(callback, feedback_confirmation)
        await callback.answer()

    @dp.message(lambda message: message.text == "📅 Записаться на экскурсию", UserState.main_menu)
    async def start_booking_tour(message: types.Message, state: FSMContext):
        """Запуск процесса записи на экскурсию."""
        response = "Выберите удобное время для экскурсии:"
        inline_kb = get_tour_time_keyboard()
        await message.reply(response, reply_markup=inline_kb)
        await state.set_state(UserState.booking_tour)

    @dp.callback_query(lambda c: c.data == "go_to_book_tour")
    async def go_to_book_tour(callback: types.CallbackQuery, state: FSMContext):
        """Переход в раздел 'Записаться на экскурсию'."""
        response = "Выберите удобное время для экскурсии:"
        inline_kb = get_tour_time_keyboard()
        await callback.message.delete()
        await callback.message.answer(response, reply_markup=inline_kb)
        await state.set_state(UserState.booking_tour)
        await callback.answer()

    @dp.callback_query(lambda c: c.data.startswith("tour_time_"), UserState.booking_tour)
    async def process_tour_booking(callback: types.CallbackQuery, state: FSMContext):
        """Сохранение записи на экскурсию в базе данных."""
        time_slot = callback.data.replace("tour_time_", "").replace("_", ":")
        user_id = callback.message.chat.id
        date = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            museum_database.save_booking(user_id, time_slot, date, timestamp)
            logger.info(f"Запись на экскурсию сохранена в базе данных: user_id={user_id}, time_slot={time_slot}, date={date}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении записи на экскурсию в базе данных: {e}")
            await callback.message.reply("Произошла ошибка при записи на экскурсию. Попробуйте снова.")
            return

        response = f"Вы успешно записаны на экскурсию в {time_slot}! 🎉 Мы ждем вас!"
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Озвучить подтверждение", callback_data="voice_booking_confirmation")]
        ])
        navigation = get_navigation_keyboard(exclude_section="go_to_book_tour")
        inline_kb.inline_keyboard.extend(navigation.inline_keyboard)
        await state.update_data(booking_confirmation=response)
        await callback.message.edit_text(response, reply_markup=inline_kb)
        await state.set_state(UserState.main_menu)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "voice_booking_confirmation")
    async def voice_booking_confirmation(callback: types.CallbackQuery, state: FSMContext):
        """Озвучивание подтверждения записи на экскурсию."""
        data = await state.get_data()
        booking_confirmation = data.get("booking_confirmation", "Подтверждение недоступно.")
        await send_voice_message(callback, booking_confirmation)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "back_to_menu")
    async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
        """Возврат в главное меню с отправкой нового сообщения."""
        await callback.message.delete()
        await callback.message.answer("Вы вернулись в главное меню.", reply_markup=get_main_menu())
        await state.set_state(UserState.main_menu)
        await callback.answer()

    @dp.message(lambda message: message.text == "🔙 В начало")
    async def reset_to_menu(message: types.Message, state: FSMContext):
        """Ручной сброс в главное меню."""
        await message.reply("Вы вернулись в главное меню.", reply_markup=get_main_menu())
        await state.set_state(UserState.main_menu)

    @dp.message()
    async def handle_free_text(message: types.Message, state: FSMContext):
        """Умная обработка текста без нажатия кнопок."""
        current_state = await state.get_state()
        if current_state == UserState.main_menu.state:
            text = message.text.lower()
            if "зал" in text:
                await start_halls_exploration(message, state)
            elif "экспонат" in text or "картин" in text:
                await start_exhibits_exploration(message, state)
            elif "маршрут" in text or "путь" in text or "как пройти" in text:
                await start_hall_to_hall_navigation(message, state)
            elif "вопрос" in text or "?" in text or "поиск" in text or "найти" in text:
                await start_asking(message, state)
            elif "отзыв" in text:
                await start_leaving_feedback(message, state)
            elif "экскурсия" in text:
                await start_booking_tour(message, state)
            else:
                await message.reply("Не понял, выбери из меню или уточни!", reply_markup=get_main_menu())