import sqlite3
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
import qrcode
import time

# Загрузка конфигурации
with open("museum_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

museum_name = config["museum_name"]
translations = config["translations"]
available_languages = config["languages"]
nodes_config = config["nodes"]
routes_config = config["routes"]
tours_config = config["tours"]
bot_username = "GuideMeMuseum_bot"  # Укажите имя вашего бота

user_language = {}
user_state = {}  # Для отслеживания состояния диалога
user_interest = {}  # Для хранения интересов пользователя
user_current_location = {}  # Для хранения текущего местоположения
user_selected_exhibition = {}  # Для хранения выбранной выставки

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("museum.db")
    cursor = conn.cursor()

    # Таблица узлов
    cursor.execute('''CREATE TABLE IF NOT EXISTS nodes (
        qr_id TEXT PRIMARY KEY,
        name_ru TEXT,
        name_en TEXT,
        theme TEXT,
        description_ru TEXT,
        description_en TEXT
    )''')

    # Таблица маршрутов
    cursor.execute('''CREATE TABLE IF NOT EXISTS routes (
        from_node TEXT,
        to_node TEXT,
        route_description_ru TEXT,
        route_description_en TEXT,
        FOREIGN KEY(from_node) REFERENCES nodes(qr_id),
        FOREIGN KEY(to_node) REFERENCES nodes(qr_id)
    )''')

    # Таблица экскурсий
    cursor.execute('''CREATE TABLE IF NOT EXISTS tours (
        user_id TEXT,
        tour_id TEXT,
        tour_name TEXT
    )''')

    # Таблица отзывов
    cursor.execute('''CREATE TABLE IF NOT EXISTS feedback (
        user_id TEXT,
        feedback_text TEXT,
        timestamp TEXT
    )''')

    # Добавляем узлы
    for node in nodes_config:
        cursor.execute("INSERT OR IGNORE INTO nodes (qr_id, name_ru, name_en, theme, description_ru, description_en) VALUES (?, ?, ?, ?, ?, ?)",
                       (node["qr_id"], node["name"]["ru"], node["name"]["en"], node["theme"], node["description"]["ru"], node["description"]["en"]))

    # Добавляем маршруты
    for route in routes_config:
        cursor.execute("INSERT OR IGNORE INTO routes (from_node, to_node, route_description_ru, route_description_en) VALUES (?, ?, ?, ?)",
                       (route["from_node"], route["to_node"], route["route_description"]["ru"], route["route_description"]["en"]))

    conn.commit()
    conn.close()

# Генерация QR-кодов
def generate_qr_codes():
    for node in nodes_config:
        qr_id = node["qr_id"]
        qr_data = f"https://t.me/{bot_username}?start={qr_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")
        img.save(f"{qr_id}_qr.png")

# Функция для преобразования текста в голос
def text_to_speech(text, lang="ru"):
    filename = f"response_{int(time.time())}.mp3"
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    return filename

# Получение информации о местоположении
def get_node_info(qr_id, lang="ru"):
    conn = sqlite3.connect("museum.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT name_{lang}, description_{lang} FROM nodes WHERE qr_id = ?", (qr_id,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (qr_id, "Description not found")

# Поиск выставки по интересам
def find_exhibition_by_theme(theme, lang="ru"):
    conn = sqlite3.connect("museum.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT qr_id, name_{lang}, description_{lang} FROM nodes WHERE theme LIKE ? AND theme NOT IN ('вход', 'переход')", (f"%{theme}%",))
    result = cursor.fetchone()
    conn.close()
    return result

# Поиск маршрута
def find_route(from_node, to_node, lang="ru"):
    conn = sqlite3.connect("museum.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT route_description_{lang} FROM routes WHERE from_node = ? AND to_node = ?", (from_node, to_node))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Route not found."

# Сохранение отзыва
def save_feedback(user_id, feedback_text):
    conn = sqlite3.connect("museum.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feedback (user_id, feedback_text, timestamp) VALUES (?, ?, ?)",
                   (str(user_id), feedback_text, time.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# Сохранение записи на экскурсию
def book_tour(user_id, tour_id, tour_name):
    conn = sqlite3.connect("museum.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tours (user_id, tour_id, tour_name) VALUES (?, ?, ?)",
                   (str(user_id), tour_id, tour_name))
    conn.commit()
    conn.close()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_language[user_id] = "ru"  # По умолчанию русский

    qr_id = context.args[0] if context.args else None
    if qr_id:
        user_current_location[user_id] = qr_id
        if user_state.get(user_id) == "awaiting_qr":
            exhibition = user_selected_exhibition.get(user_id)
            if exhibition:
                start_node = qr_id
                end_node = exhibition["qr_id"]
                lang = user_language.get(user_id, "ru")
                route = find_route(start_node, end_node, lang)
                response = translations[lang]["route"].format(route=route)
                user_state[user_id] = "menu"
                await update.message.reply_text(response)
                audio_file = text_to_speech(response, lang=lang)
                with open(audio_file, "rb") as audio:
                    await update.message.reply_voice(audio)
                # Возвращаемся в меню
                response = translations[lang]["menu"]
                keyboard = [["1️⃣"], ["2️⃣"], ["3️⃣"], ["4️⃣"], ["5️⃣"], ["6️⃣"]]
                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
                await update.message.reply_text(response, reply_markup=reply_markup)
            return

    user_state[user_id] = "menu"
    lang = user_language.get(user_id, "ru")
    response = translations[lang]["welcome"].format(museum_name=museum_name)
    keyboard = [["1️⃣"], ["2️⃣"], ["3️⃣"], ["4️⃣"], ["5️⃣"], ["6️⃣"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(response, reply_markup=reply_markup)

    audio_file = text_to_speech(response, lang=lang)
    with open(audio_file, "rb") as audio:
        await update.message.reply_voice(audio)

# Команда /language
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = user_language.get(user_id, "ru")
    response = translations[lang]["language"]
    keyboard = [[lang] for lang in available_languages]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(response, reply_markup=reply_markup)

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = user_language.get(user_id, "ru")
    text = update.message.text.lower()

    # Проверка выбора языка
    if text in available_languages:
        user_language[user_id] = text
        response = translations[text]["welcome"].format(museum_name=museum_name)
        user_state[user_id] = "menu"
        keyboard = [["1️⃣"], ["2️⃣"], ["3️⃣"], ["4️⃣"], ["5️⃣"], ["6️⃣"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text(response, reply_markup=reply_markup)
        audio_file = text_to_speech(response, lang=text)
        with open(audio_file, "rb") as audio:
            await update.message.reply_voice(audio)
        return

    state = user_state.get(user_id, "menu")

    if state == "menu":
        if text == "1️⃣":
            user_state[user_id] = "awaiting_interest"
            response = translations[lang]["exhibitions"]
            await update.message.reply_text(response)
        elif text == "2️⃣":
            user_state[user_id] = "awaiting_interest"
            response = translations[lang]["exhibitions"]
            await update.message.reply_text(response)
        elif text == "3️⃣":
            response = translations[lang]["info_menu"]
            await update.message.reply_text(response)
        elif text == "4️⃣":
            user_state[user_id] = "booking_tour"
            response = translations[lang]["book_tour"]
            keyboard = [["1️⃣"], ["2️⃣"], ["3️⃣"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(response, reply_markup=reply_markup)
        elif text == "5️⃣":
            user_state[user_id] = "awaiting_feedback"
            response = translations[lang]["feedback"]
            await update.message.reply_text(response)
        elif text == "6️⃣":
            response = translations[lang]["language"]
            keyboard = [[lang] for lang in available_languages]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(response, reply_markup=reply_markup)
        else:
            response = translations[lang]["menu"]
            keyboard = [["1️⃣"], ["2️⃣"], ["3️⃣"], ["4️⃣"], ["5️⃣"], ["6️⃣"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(response, reply_markup=reply_markup)

    elif state == "awaiting_interest":
        user_interest[user_id] = text
        exhibition = find_exhibition_by_theme(text, lang)
        if exhibition:
            qr_id, name, description = exhibition
            user_state[user_id] = "awaiting_route_confirmation"
            user_selected_exhibition[user_id] = {"qr_id": qr_id, "name": name, "description": description}
            response = translations[lang]["suggest_exhibition"].format(name=name, location=qr_id)
            keyboard = [["Да"], ["Нет"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(response, reply_markup=reply_markup)
        else:
            response = translations[lang]["unknown_interest"]
            await update.message.reply_text(response)

    elif state == "awaiting_route_confirmation":
        if text == "да":
            user_state[user_id] = "awaiting_qr"
            response = translations[lang]["scan_qr"]
            await update.message.reply_text(response)
        else:
            user_state[user_id] = "menu"
            response = translations[lang]["menu"]
            keyboard = [["1️⃣"], ["2️⃣"], ["3️⃣"], ["4️⃣"], ["5️⃣"], ["6️⃣"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(response, reply_markup=reply_markup)

    elif state == "booking_tour":
        tour_id = text.replace("️⃣", "")
        tour = next((t for t in tours_config if t["id"] == tour_id), None)
        if tour:
            tour_name = tour["name"][lang]
            book_tour(user_id, tour_id, tour_name)
            response = translations[lang]["tour_booked"].format(tour=tour_name)
            user_state[user_id] = "menu"
            await update.message.reply_text(response)
            response = translations[lang]["menu"]
            keyboard = [["1️⃣"], ["2️⃣"], ["3️⃣"], ["4️⃣"], ["5️⃣"], ["6️⃣"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(response, reply_markup=reply_markup)
        else:
            response = translations[lang]["book_tour"]
            keyboard = [["1️⃣"], ["2️⃣"], ["3️⃣"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(response, reply_markup=reply_markup)

    elif state == "awaiting_feedback":
        save_feedback(user_id, text)
        response = translations[lang]["feedback_thanks"]
        user_state[user_id] = "menu"
        await update.message.reply_text(response)
        response = translations[lang]["menu"]
        keyboard = [["🏠 Главное меню"], ["1️⃣Узнать о выставках"], ["2️⃣Навигация"], ["3️⃣Информация о музее"], ["4️⃣аписаться на экскурсию"], ["5️⃣Оставить отзыв"], ["6️⃣Сменить язык"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await update.message.reply_text(response, reply_markup=reply_markup)

    audio_file = text_to_speech(response, lang=lang)
    with open(audio_file, "rb") as audio:
        await update.message.reply_voice(audio)

# Основная функция
def main():
    init_db()
    generate_qr_codes()

    application = Application.builder().token("7440624971:AAG5lISWjLOI6qMMnc-QSrW4uWz_9s2WLG8").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("language", language))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()