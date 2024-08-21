from PIL import Image, ImageDraw
from pdf2image import convert_from_path
import json
import os

from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS

import base64

app = Flask(__name__)
CORS(app)



def extract_pdf_data():
    # Extracting data from PDF

    # check the body of the request


    if request.data:
        # print("Request data: ", request.data)
        data = request.get_json()
        # access the "is_local" key
        if "pdf_data" in data:
            # pdf_data is in base64 format, decode it and save it to a file
            pdf_data = data["pdf_data"]

            # Remove the "data:application/pdf;base64," prefix if it exists
            if pdf_data.startswith("data:application/pdf;base64,"):
                pdf_data = pdf_data[len("data:application/pdf;base64,"):]

            # Decode the base64 data
            decoded_pdf_data = base64.b64decode(pdf_data)

            # Save the decoded data to a PDF file
            with open("output.pdf", "wb") as pdf_file:
                pdf_file.write(decoded_pdf_data)

            



    current_dir = ""
    # if request.data:
    #     print("Request data: ", request.data)
    #     data = request.get_json()
    #     print("Data: ", data)
    #     # access the "is_local" key
    #     if "is_local" in data:
    #         is_local = data["is_local"]
    #         if not is_local:
    #             current_dir = "mysite/"
    filename = "output"
    # filename = f"{current_dir}{filename}"


    # if not os.path.exists(f"{filename}.pdf"):
    #     return json.dumps({
    #         "error": "File not found", 
    #         "files": os.listdir(current_dir), 
    #         "path": current_dir + filename}
    #     )
    

    

    
    pages = None
    try:
        pages = convert_from_path(f"{filename}.pdf", 500)
    except Exception as e:
        info_obj = {
            "error": str(e),
            "files": os.listdir(current_dir),
            "path": current_dir + filename
        }

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

    # for i in range(rows):
    #     print(grid[i])

    # delete the image file
    os.remove(image_file_path)
    os.remove("output.pdf")

    return json.dumps(dict_info)


@app.route('/')
def home():
    return 'windows'

@app.route('/extract', methods=['GET', 'POST'])
def extract():
    return extract_pdf_data()

if __name__ == '__main__':
    app.run(debug=True)
