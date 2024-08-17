from PIL import Image, ImageDraw
from pdf2image import convert_from_path
import json
import os

from pathlib import Path

from flask import Flask
app = Flask(__name__)


def extract_pdf_data(filename : str):
    # Extracting data from PDF

    filename = f"{filename}"
    if not os.path.exists(f"{filename}.pdf"):
        current_dir = "."
        current_dir_files = os.listdir(current_dir)
        return json.dumps({"error": "File not found", "files": current_dir_files}, indent=4)

    
    current_dir = "."
    poppler_dir = ""
    full_dir = ""
    for f in os.listdir(current_dir):
        if f.startswith("poppler-"):
            poppler_dir = f
            full_dir = f"./{f}/Library/bin"
            break
    
    pages = None
    try:
        pages = convert_from_path(f"{filename}.pdf", 500, poppler_path=full_dir)
    except Exception as e:
        info_obj = {
            "error": str(e),
            "full_dir": full_dir,
            "files": os.listdir(full_dir)
        }
        # for f in os.listdir(current_dir):
        #     if f.startswith("poppler-"):
        #         info_obj["poppler_dir_files"] = os.listdir(f"{current_dir}/{f}/Library")
        #         info_obj["poppler_dir_files_bin"] = os.listdir(f"{current_dir}/{f}/Library/bin")
        #         break
        return json.dumps(info_obj, indent=4)
    image_file_path = f"{filename}.jpg"
    for count, page in enumerate(pages):
        if count == 1:
            page.save(image_file_path, 'JPEG')

    im = Image.open(image_file_path)

    # crop_rectangle = (810, 405, 1180, 650)
    crop_rectangle = (2690, 1350, 3880, 2170)
    cropped_im = im.crop(crop_rectangle)

    rows = 9
    columns = 6

    cell_width = cropped_im.size[0] // (columns)
    cell_height = cropped_im.size[1] // (rows)

    grid = [ [0]*columns for _ in range(rows) ]

    # # Loop through each cell, check for each pixel if there is a color value < 100, if so mark it as 1
    #
    for i in range(rows):
        for j in range(columns):
            count = 0
            for x in range(cell_width):
                for y in range(cell_height):
                    pixel = cropped_im.getpixel((j*cell_width + x, i*cell_height + y))
                    # pixel returns a RGB tuple (r, g, b)
                    is_black = True
                    for p in pixel:
                        if p > 0:
                            is_black = False
                            break
                    if is_black:
                        count = 1
            grid[i][j] = count

    dict_info = {
        "data" : grid
    }


    # with open(f"{filename}.json", "w") as outfile:
    # 	json.dump(dict_info, outfile)

    for i in range(rows):
        print(grid[i])

    # delete the image file
    os.remove(image_file_path)

    return json.dumps(dict_info)


@app.route('/')
def home():
    return 'windows'

@app.route('/extract/<filename>')
def extract(filename):
    return extract_pdf_data(filename)

if __name__ == '__main__':
    app.run(debug=True)
