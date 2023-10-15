import os
import fitz
from PIL import Image, ImageDraw, ImageFont
import pytesseract

# Установите путь к исполняемому файлу Tesseract OCR (если он не находится в системном PATH)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
font_paths = ['fonts/arial.ttf', 'fonts/GOST_EE.ttf', 'fonts/GOST.TTF', 'fonts/GOST_SLIDE.ttf', 'fonts/BGOST.ttf']
fonts = [ImageFont.truetype(font_path, 36, encoding="unic") for font_path in font_paths]

def find_and_replace_text(img, old_code, new_code, file_count):
    recognized_data = pytesseract.image_to_data(img, lang='eng+rus', output_type=pytesseract.Output.DICT)
    draw = ImageDraw.Draw(img)
    n_boxes = len(recognized_data['text'])
    for i in range(n_boxes):
        text = recognized_data['text'][i]
        conf = int(recognized_data['conf'][i])
        if conf > 0 and old_code in text:
            (x, y, w, h) = (recognized_data['left'][i], recognized_data['top'][i], recognized_data['width'][i], recognized_data['height'][i])
            # Нарисовать прямоугольник вокруг найденного текста с желтым контуром
            draw.rectangle([(x, y), (x + w, y + h)], outline="yellow", width=3)
            font = fonts[file_count % len(fonts)]
            new_text = f"{new_code}-{file_count}"
            draw.text((x, y), new_text, font=font, fill="black")
            file_count += 1

def process_image(img, old_code, new_code, file_count):
    find_and_replace_text(img, old_code, new_code, file_count)

def process_pdf(pdf_path, old_code, new_code, output_folder, file_count):
    pdf_document = fitz.open(pdf_path)

    for page_number in range(pdf_document.page_count):
        page = pdf_document[page_number]
        page_pixmap = page.get_pixmap()
        img = Image.frombytes("RGB", [page_pixmap.width, page_pixmap.height], page_pixmap.samples)
        process_image(img, old_code, new_code, file_count)

        image_filename = os.path.join(output_folder, f"page_{page_number + 1}.png")
        img.save(image_filename)

    return file_count

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
            file_count = process_pdf(input_path, old_code, new_code, output_folder, file_count)
            modified = True

    if modified:
        print("Измененные файлы были сохранены.")
    else:
        print("Ни один файл не был изменен.")

if __name__ == "__main__":
    input_folder = input("Введите путь к папке с чертежами: ")
    output_folder = input("Введите путь для сохранения обработанных чертежей: ")

    main(input_folder, output_folder)
