import os
import fitz
from PIL import Image, ImageDraw
import easyocr
import numpy as np

font_paths = [
    'fonts/arial.ttf',
    'fonts/GOST_EE.ttf',
    'fonts/GOST.TTF',
    'fonts/GOST_SLIDE.ttf',
    'fonts/BGOST.ttf'
]

def detect_text_orientation(bound):
    center_y = (bound[0][1] + bound[2][1]) / 2
    return "flipped" if center_y < 0.5 else "normal"

def rotate_text(image, angle):
    return image.rotate(angle, expand=True)

def resize_image(img, target_width=1920, target_height=1080):
    width, height = img.size
    if width > target_width or height > target_height:
        img = img.resize((target_width, target_height))
    return img

def find_and_replace_text(img, search_texts, new_code, file_count, sub_count):
    reader = easyocr.Reader(['en', 'ru'], gpu=True)
    bounds = reader.readtext(np.array(img))
    draw = ImageDraw.Draw(img)
    replaced = False

    for bound in bounds:
        text = bound[1]
        orientation = detect_text_orientation(bound[0])

        if orientation == "flipped":
            continue

        for search_text in search_texts:
            if search_text in text:
                box = bound[0]
                (x, y, w, h) = box[0][0], box[0][1], box[2][0] - box[0][0], box[2][1] - box[0][1]
                draw.rectangle([(x, y), (x + w, y + h)], outline="white", width=3, fill="white")
                new_text = f"{new_code}-{file_count}"
                if sub_count > 0:
                    new_text += f"-{sub_count}"
                draw.text((x, y), new_text, fill="black", encoding="utf-8")

                replaced = True
                break

    if replaced:
        sub_count += 1
        file_count += 1

    return img, replaced, file_count, sub_count

def process_image(img, search_texts, new_code, file_count, sub_count):
    resized_img = resize_image(img)
    resized_img, text_replaced, file_count, sub_count = find_and_replace_text(resized_img, search_texts, new_code, file_count, sub_count)
    return resized_img, text_replaced, file_count, sub_count

def process_pdf(pdf_path, search_texts, new_code, output_folder, file_count, sub_count):
    pdf_document = fitz.open(pdf_path)

    for page_number in range(pdf_document.page_count):
        page = pdf_document[page_number]
        page_pixmap = page.get_pixmap()
        img = Image.frombytes("RGB", [page_pixmap.width, page_pixmap.height], page_pixmap.samples)
        resized_img, text_replaced, file_count, sub_count = process_image(img, search_texts, new_code, file_count, sub_count)

        if text_replaced:
            image_filename = os.path.join(output_folder, f"page_{file_count}.png")
            resized_img.save(image_filename)
            print(f"Текст на странице {page_number + 1} был найден и заменен.")

    return file_count, sub_count

def main(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    search_text = input("Введите текст для поиска: ")
    new_code = input("Введите новый шифр для замены: ")
    file_count = 1
    sub_count = 1
    modified = False

    for file_name in os.listdir(input_folder):
        input_path = os.path.join(input_folder, file_name)

        if file_name.lower().endswith((".jpg", ".png")):
            img = Image.open(input_path)
            rotated_img = rotate_text(img, 90)
            processed_img, text_replaced, file_count, sub_count = process_image(rotated_img, [search_text], new_code, file_count, sub_count)

            if text_replaced:
                modified = True
                output_filename = os.path.join(output_folder, f"{file_count}.png")
                processed_img.save(output_filename)
                print(f"Файл '{file_name}' был изменен.")

        elif file_name.lower().endswith((".pdf")):
            file_count, sub_count = process_pdf(input_path, [search_text], new_code, output_folder, file_count, sub_count)
            modified = True
            print(f"Файл '{file_name}' был изменен.")

    if modified:
        print("Измененные файлы были сохранены.")
    else:
        print("Ни один файл не был изменен.")

if __name__ == "__main__":
    input_folder = input("Введите путь к папке с чертежами: ")
    output_folder = input("Введите путь для сохранения обработанных чертежей: ")

    main(input_folder, output_folder)
