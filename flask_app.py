from PIL import Image, ImageDraw
from pdf2image import convert_from_path
import json
import os

from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS

import base64
from dotenv import load_dotenv

from openai import OpenAI


from langchain_community.document_loaders import PyPDFLoader



app = Flask(__name__)
CORS(app)
load_dotenv()
client = OpenAI(
    api_key=os.getenv("API_KEY")
    )


def extract_pdf_data():
    

    if request.data:
        # print("Request data: ", request.data)
        data = request.get_json()
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

    current_dir = ""
    filename = "output"


    pages = None
    try:
        pages = convert_from_path(f"{filename}.pdf", 500)
    except Exception as e:
        info_obj = {
            "error": str(e),
            "mysite_files" : os.listdir("mysite/"),
            "root_files" : os.listdir("/"),
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

    # delete the image file and pdf file
    os.remove(image_file_path)
    os.remove("output.pdf")

    return json.dumps(dict_info)


def gpt():


    load_dotenv()

    
    try:

        if request.data:
            # print("Request data: ", request.data)
            data = request.get_json()
            # access the "is_local" key
            if "pdf_data" in data:
                # pdf_data is in base64 format, decode it and save it to a file
                pdf_data = data["pdf_data"]


                if pdf_data.startswith("data:application/pdf;base64,"):
                    pdf_data = pdf_data[len("data:application/pdf;base64,"):]

                # Decode the base64 data
                decoded_pdf_data = base64.b64decode(pdf_data)

                # Save the decoded data to a PDF file
                with open("adviesbox.pdf", "wb") as pdf_file:
                    pdf_file.write(decoded_pdf_data)
    except Exception as e:
        return "Error saving the pdf file"

    pdf = "adviesbox.pdf"

    loader = None
    try:
        loader = PyPDFLoader(pdf)
    except Exception as e:
        return "Error loading the pdf file"
    
    documents = None
    try:
        documents = loader.load()
    except Exception as e:
        return "Error loading the documents"


    question = """
    In het document, is het een huurwoning? Zo ja, wat is de huurprijs per maand. Zo niet, beantwoord deze vragen met behulp van sectie 2.1 in het document: Is de woning bedoeld voor blijven te wonen(primaire woning) of verkoop of verhuur? Is de woning verkocht? Wat is de verwachte verkoopwaarde(marktwaarde)? Wat zijn de verkoopkosten? Wat is de WOZ-waarde? Geef een json object terug met de volgende template:{ "type": string ("eigen", "huur", "inwonend"), "huurprijs" : int, "doel_woning": string, ("wonen", "verkoop", "verhuur") "is_verkocht": Boolean, "verkoopwaarde": int, "verkoopkosten": int, "woz" : int }. Gebruik geen text of iets, het enige wat ik wil krijgen is het json object, zonder apostrophe erbij(`). Dit zal worden gebruiktt in een API request dus ik moet het direct kunnen gebruiken als json object in python
    """

    # using the pdf's content in documents, and the question, use gpt-4o to answer the question

    # make documents a string


    doc_strings = [x.dict()['page_content'] for x in documents]
    
    pdf_string = " ".join(doc_strings)



    answer = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": question + " Here is the content of the pdf: " + pdf_string
            }
        ]
    )

    print(answer.choices[0].message.content)
    woningsituatie = json.loads(answer.choices[0].message.content)
    print(woningsituatie)

    return woningsituatie

@app.route('/')
def home():
    return 'windows'

@app.route('/extract', methods=['GET', 'POST'])
def extract():
    return extract_pdf_data()


@app.route('/adviesbox', methods=['GET', 'POST'])
def adviesbox():
    return gpt()


def main():
    load_dotenv()
    
    gpt()

if __name__ == '__main__':
    app.run(debug=True)
    # main()
