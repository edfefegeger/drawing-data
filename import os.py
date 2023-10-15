import os
import fitz
from PIL import Image, ImageDraw, ImageFont
import pytesseract

# Установите путь к исполняемому файлу Tesseract OCR (если он не находится в системном PATH)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def process_image(img, old_code, new_code, file_count):
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 36, encoding="unic")

    # Используем Tesseract для распознавания текста на изображении
    recognized_text = pytesseract.image_to_string(img, lang='eng+rus')

    # Находим все вхождения старого кода и заменяем их новым кодом
    occurrences = recognized_text.count(old_code)
    start = 0
    for i in range(occurrences):
        index = recognized_text.find(old_code, start)
        if index == -1:
            break
        x, y = img.width // 2, index // img.width
        draw.rectangle([(x, y), (x + len(old_code) * 20, y + 40)], fill="white")
        draw.text((x, y), f"{new_code}-{file_count}-{i+1}", font=font, fill="black")
        start = index + len(old_code)

def process_pdf(pdf_path, old_code, new_code, output_folder, file_count):
    pdf_document = fitz.open(pdf_path)

    for page_number in range(pdf_document.page_count):
        page = pdf_document[page_number]
        page_pixmap = page.get_pixmap()
        img = Image.frombytes("RGB", [page_pixmap.width, page_pixmap.height], page_pixmap.samples)
        process_image(img, old_code, new_code, file_count)

        image_filename = os.path.join(output_folder, f"page_{page_number + 1}.png")
        img.save(image_filename)

def main(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    old_code = input("Введите старый шифр для поиска: ")
    new_code = input("Введите новый шифр для замены: ")
    file_count = 1
    modified = False

    for file_name in os.listdir(input_folder):
        input_path = os.path.join(input_folder, file_name)
        output_path = os.path.join(output_folder, file_name)

        if file_name.lower().endswith((".jpg", ".png")):
            img = Image.open(input_path)
            processed_img = img.copy()  # Создаем копию изображения для обработки
            process_image(processed_img, old_code, new_code, file_count)

            if processed_img.tobytes() != img.tobytes():  # Проверяем, были ли изменения
                modified = True
                processed_img.save(output_path)
                file_count += 1

        elif file_name.lower().endswith((".pdf")):
            process_pdf(input_path, old_code, new_code, output_folder, file_count)
            modified = True
            file_count += 1

    if modified:
        print("Измененные файлы были сохранены.")
    else:
        print("Ни один файл не был изменен.")

if __name__ == "__main__":
    input_folder = input("Введите путь к папке с чертежами: ")
    output_folder = input("Введите путь для сохранения обработанных чертежей: ")

    main(input_folder, output_folder)
