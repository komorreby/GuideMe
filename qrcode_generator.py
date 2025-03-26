import qrcode
import os
from database import museum_database

def generate_qr_codes(output_dir: str = "qr_codes"):
    """
    Генерирует QR-коды для всех залов музея и сохраняет их в указанную папку.

    Args:
        output_dir (str): Папка для сохранения QR-кодов.
    """
    # Создаём папку для QR-кодов, если её нет
    os.makedirs(output_dir, exist_ok=True)

    # Получаем все залы из базы данных
    halls = museum_database.get_all_halls()

    # Telegram-ссылка на бота (замените @YourBot на реальный username вашего бота)
    bot_link = "https://t.me/GuideMeMuseum_bot?start=hall_{hall_id}"

    for hall in halls:
        hall_id = hall["id"]
        hall_name = hall["name"]

        # Формируем ссылку для QR-кода
        qr_link = bot_link.format(hall_id=hall_id)

        # Создаём QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_link)
        qr.make(fit=True)

        # Создаём изображение QR-кода
        img = qr.make_image(fill_color="black", back_color="white")

        # Сохраняем QR-код в файл
        file_path = os.path.join(output_dir, f"hall_{hall_id}_{hall_name}.png")
        img.save(file_path)
        print(f"QR-код для зала '{hall_name}' сохранён в {file_path}")

if __name__ == "__main__":
    generate_qr_codes()