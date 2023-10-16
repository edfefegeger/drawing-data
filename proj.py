import os
import fitz
from PIL import Image, ImageDraw, ImageFont
import pytesseract

# Установите путь к исполняемому файлу Tesseract OCR (если он не находится в системном PATH)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Загрузите все шрифты, включая специальные шрифты для текста в наклоне
font_paths = [
    'fonts/arial.ttf',
    'fonts/GOST_EE.ttf',
    'fonts/GOST.TTF',
    'fonts/GOST_SLIDE.ttf',
    'fonts/BGOST.ttf'
]

def find_and_replace_text(img, search_texts, new_code, file_count):
    recognized_data = pytesseract.image_to_data(img, lang='en+rus', output_type=pytesseract.Output.DICT)
    draw = ImageDraw.Draw(img)
    n_boxes = len(recognized_data['text'])
    font_path = font_paths[file_count % len(font_paths)]
    font = ImageFont.truetype(font_path, 20, encoding="unic")
    replaced = False  # Флаг, который указывает, были ли внесены изменения

    for i in range(n_boxes):
        text = recognized_data['text'][i]
        conf = int(recognized_data['conf'][i])
        for search_text in search_texts:
            if conf > -1000 and search_text in text:
                (x, y, w, h) = (recognized_data['left'][i], recognized_data['top'][i], recognized_data['width'][i], recognized_data['height'][i])
                # Нарисовать прямоугольник вокруг найденного текста с белым заливкой
                draw.rectangle([(x, y), (x + w, y + h)], outline="white", width=3, fill="white")
                new_text = f"{new_code}-{file_count}"
                draw.text((x, y), new_text, font=font, fill="black")
                replaced = True

    if replaced:
        file_count += 1

    return img, replaced, file_count


def process_image(img, search_texts, new_code, file_count):
    replaced = False
    for search_text in search_texts:
        img, text_replaced, file_count = find_and_replace_text(img, [search_text], new_code, file_count)
        replaced = replaced or text_replaced
    return img, replaced, file_count


def process_pdf(pdf_path, search_texts, new_code, output_folder, file_count):
    pdf_document = fitz.open(pdf_path)

    for page_number in range(pdf_document.page_count):
        page = pdf_document[page_number]
        page_pixmap = page.get_pixmap()
        img = Image.frombytes("RGB", [page_pixmap.width, page_pixmap.height], page_pixmap.samples)
        process_image(img, search_texts, new_code, file_count)

        image_filename = os.path.join(output_folder, f"page_{page_number + 1}.png")
        img.save(image_filename)

    return file_count

def main(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    search_text = input("Введите текст для поиска: ")
    new_code = input("Введите новый шифр для замены: ")
    file_count = 1
    modified = False

    for file_name in os.listdir(input_folder):
        input_path = os.path.join(input_folder, file_name)
        output_path = os.path.join(output_folder, file_name)

        if file_name.lower().endswith((".jpg", ".png")):
            img = Image.open(input_path)
            processed_img = img.copy()  # Создаем копию изображения для обработки
            processed_img, text_replaced, file_count = process_image(processed_img, [search_text], new_code, file_count)

            if text_replaced:
                modified = True
                processed_img.save(output_path)

        elif file_name.lower().endswith((".pdf")):
            file_count = process_pdf(input_path, [search_text], new_code, output_folder, file_count)
            modified = True

    if modified:
        print("Измененные файлы были сохранены.")
    else:
        print("Ни один файл не был изменен.")

if __name__ == "__main__":
    input_folder = input("Введите путь к папке с чертежами: ")
    output_folder = input("Введите путь для сохранения обработанных чертежей: ")

    main(input_folder, output_folder)
