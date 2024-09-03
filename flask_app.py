from PIL import Image
from pdf2image import convert_from_path
import json
import os

from flask import Flask, request
from flask_cors import CORS

import base64
from pypdf import PdfReader


app = Flask(__name__)
CORS(app)

def extract_pdf_data():
    

    is_local = False
    if request.data:
        # print("Request data: ", request.data)
        data = request.get_json()
        is_local = data.get("is_local", False)
        # access the "is_local" key
        if "pdf_data" in data:
            # pdf_data is in base64 format, decode it and save it to a file
            pdf_data = data["pdf_data"]


            if pdf_data.startswith("data:application/pdf;base64,"):
                pdf_data = pdf_data[len("data:application/pdf;base64,"):]

            # Decode the base64 data
            decoded_pdf_data = base64.b64decode(pdf_data)

            # Save the decoded data to a PDF file
            with open("output.pdf", "wb") as pdf_file:
                pdf_file.write(decoded_pdf_data)

    current_dir = "mysite/"
    filename = "output"

    

    if is_local:
        current_dir = ""

    pages = None
    try:
        pages = convert_from_path(f"{current_dir}{filename}.pdf", 500)
    except Exception as e:
        info_obj = {
            "error": str(e),
            "mysite_files" : os.listdir("mysite/") if os.path.exists("mysite/") else [],
            "root_files" : os.listdir("."),
        }

        return json.dumps(info_obj, indent=4)
    
    image_file_path = f"{filename}_2.jpg"
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

    grid = [ [0] * columns for _ in range(rows) ]

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

    risico_data = scan_risico(filename, im)
    is_bruto = scan_is_bruto(filename, pages)
    woonsituatie = gpt()
    dict_info = {
        "data" : grid,
        "risico" : risico_data,
        "is_bruto" : is_bruto,
        "woonsituatie" : woonsituatie
    }

    print("Grid: ")	
    for i in range(len(grid)):
        print(grid[i])

    print("Risico: ")
    for i in range(len(risico_data)):
        print(risico_data[i])


    # delete the image file and pdf file
    os.remove(image_file_path)

    if request.data:
        os.remove("output.pdf")

    print("woonsituatie: ", woonsituatie)
    print("is_bruto: ", is_bruto)

    return json.dumps(dict_info)

def scan_risico(filename: str, im: Image):

    crop_rectangle = (3280, 3300, 3890, 4320)
    cropped_im = im.crop(crop_rectangle)

    rows = 6
    columns = 3

    cell_width = cropped_im.size[0] // (columns)
    cell_height = cropped_im.size[1] // (rows)

    short = 90
    tall = 250
    cell_heights = [
                    short, short, tall + 10, 
                    short + 10, tall - 50, tall - 30
                ]

    grid = [[0] * columns for _ in range(rows)]

    for i in range(rows):
        for j in range(columns):
            count = 0
            for x in range(cell_width):
                for y in range(cell_heights[i]):
                    pixel = cropped_im.getpixel((j * cell_width + x, sum(cell_heights[:i]) + y))
                    # pixel returns a RGB tuple (r, g, b)
                    is_black = True
                    for p in pixel:
                        if p > 0:
                            is_black = False
                            break
                    if is_black:
                        count = 1
            grid[i][j] = count

    return grid

def scan_is_bruto(filename: str, pages : list):

    image_file_path = f"{filename}_1.jpg"
    for count, page in enumerate(pages):
        if count == 0:
            page.save(image_file_path, 'JPEG')

    im = Image.open(image_file_path)

    # left, top, right, bottom
    crop_rectangle = (200, 5290, 280, 5460)
    cropped_im = im.crop(crop_rectangle)

    height = cropped_im.size[1]

    box_length = 50
    offset = 15

    cropped_im_box_1 = cropped_im.crop( (offset, offset, box_length + offset, box_length + offset) )
    cropped_im_box_2 = cropped_im.crop(  (offset, 110, box_length + offset, 110 + box_length - offset) )


    grid = [0, 0]

    for x in range(box_length):
        for y in range(box_length):
            pixel = cropped_im_box_1.getpixel((x, y))
            # pixel returns a RGB tuple (r, g, b)
            is_black = True
            for p in pixel:
                if p > 0:
                    is_black = False
                    break
            if is_black:
                grid[0] = 1

    for x in range(box_length):
        for y in range(box_length - offset):
            pixel = cropped_im_box_2.getpixel((x, y))
            # pixel returns a RGB tuple (r, g, b)
            is_black = True
            for p in pixel:
                if p > 0:
                    is_black = False
                    break
            if is_black:
                grid[1] = 1


    os.remove(image_file_path)

    is_bruto = grid[0]
    is_netto = grid[1]

    print("Bruto netto grid: ")
    for i in range(len(grid)):
        print(grid[i])

    if is_bruto:
        return True
    return False


def gpt():

    pdf = "output.pdf"
    reader = PdfReader(pdf)
    fields = reader.get_form_text_fields()

    woonsituatie = {
        "totaal_inkomen" : fields.get("Totaal maandelijks inkomen") or 0,
        "huurlasten" : fields.get("Hyptoheek/Huurlasten") or 0,
        "kosten_levensonderhoud" : fields.get("Kosten voor levensonderhoud") or 0,
        "max_maandlast" : fields.get("Maximale acceptable maandlast") or 0,
    }

    for k, v in woonsituatie.items():
        woonsituatie[k] = int(v)

    return woonsituatie

@app.route('/')
def home():
    return 'windows'

@app.route('/extract', methods=['GET', 'POST'])
def extract():
    return extract_pdf_data()



if __name__ == '__main__':
    app.run(debug=True)
    # main()
