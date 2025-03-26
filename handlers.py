from aiogram import types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database import museum_database
from ai_assistant import get_ai_response

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
        """Запуск исследования залов с инлайн-кнопками."""
        await message.reply("Выберите зал для исследования:", reply_markup=get_hall_navigation())
        await state.set_state(UserState.exploring_halls)
        await state.update_data(hall_index=0)

    @dp.callback_query(lambda c: c.data.startswith("hall_"), UserState.exploring_halls)
    async def show_hall_details(callback: types.CallbackQuery, state: FSMContext):
        """Отображение информации о зале по выбору."""
        hall_id = int(callback.data.split("_")[1])
        hall = museum_database.get_hall_info(hall_id)
        if hall:
            response = f"*{hall[1]}*\n{hall[2]}\n📍 {hall[3]}\nПериод: {hall[5]}"
            await callback.message.edit_text(response, parse_mode="Markdown", reply_markup=get_hall_navigation())
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "next_hall", UserState.exploring_halls)
    async def next_hall(callback: types.CallbackQuery, state: FSMContext):
        """Переход к следующему залу автоматически."""
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
        """Запуск автоматического показа экспонатов."""
        exhibits = [museum_database.get_exhibit_info(i) for i in range(1, 6)]
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
    async def show_faq(message: types.Message):
        """Показ FAQ с возвратом в меню."""
        faqs = museum_database.get_faq()
        response = "❓ FAQ:\n\n" + "\n".join(f"❔ {q}\n💡 {a}" for q, a in faqs)
        await message.reply(response, reply_markup=get_main_menu())

    @dp.message(lambda message: message.text == "🔍 Поиск", UserState.main_menu)
    async def start_search(message: types.Message, state: FSMContext):
        """Начало поиска с подсказкой."""
        await message.reply("Назови произведение, художника или стиль!")
        await state.set_state(UserState.searching)

    @dp.message(UserState.searching)
    async def process_search(message: types.Message, state: FSMContext):
        """Обработка поиска с возвратом в меню."""
        results = museum_database.search_exhibits(message.text)
        response = "🔍 Результаты:\n\n" + (
            "\n".join(f"*{ex[2]}* ({ex[3]})\n{ex[4]}" for ex in results) if results else "Ничего не найдено."
        )
        await message.reply(response, parse_mode="Markdown", reply_markup=get_main_menu())
        await state.set_state(UserState.main_menu)

    @dp.message(lambda message: message.text == "🌍 Маршрут", UserState.main_menu)
    async def start_route(message: types.Message, state: FSMContext):
        """Интерактивный маршрут с пошаговой навигацией."""
        await state.update_data(route_step=0)
        await show_route_step(message, state)
        await state.set_state(UserState.route_navigation)

    async def show_route_step(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
        """Отображение шага маршрута."""
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
        """Навигация по шагам маршрута."""
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
        """Запуск диалога с AI."""
        await message.reply("Спроси меня об искусстве или музее!")
        await state.set_state(UserState.asking_question)

    @dp.message(UserState.asking_question)
    async def handle_question(message: types.Message, state: FSMContext):
        """Обработка вопроса с предложением продолжить."""
        response = get_ai_response(message.text)
        inline_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Ещё вопрос", callback_data="more_questions"),
             InlineKeyboardButton(text="В меню", callback_data="back_to_menu")]
        ])
        await message.reply(response, reply_markup=inline_kb)

    @dp.callback_query(lambda c: c.data == "more_questions", UserState.asking_question)
    async def more_questions(callback: types.CallbackQuery, state: FSMContext):
        """Продолжение диалога с AI."""
        await callback.message.edit_text("Задай ещё один вопрос об искусстве!", reply_markup=None)
        await callback.answer()

    @dp.callback_query(lambda c: c.data == "back_to_menu")
    async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
        """Возврат в главное меню с отправкой нового сообщения."""
        await callback.message.delete()  # Удаляем старое сообщение
        await callback.message.answer("Вы вернулись в главное меню.", reply_markup=get_main_menu())
        await state.set_state(UserState.main_menu)
        await callback.answer()

    @dp.message(lambda message: message.text == "🔙 В начало")
    async def reset_to_menu(message: types.Message, state: FSMContext):
        """Ручной сброс в главное меню."""
        await message.reply("Вы вернулись в главное меню.", reply_markup=get_main_menu())
        await state.set_state(UserState.main_menu)

    @dp.message()  # Обработка произвольного текста
    async def handle_free_text(message: types.Message, state: FSMContext):
        """Умная обработка текста без нажатия кнопок."""
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
