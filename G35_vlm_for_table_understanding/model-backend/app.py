import os
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers.pipelines import TextGenerationPipeline
import torch
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from table_extraction import process_pdf
from extract_table import extract_csv
from cloudinary_util import upload_image
from combine_csv import combine
from mode_init import load_llama3_pipeline
from csv2html import csv2html
from google import genai
import glob


import glob

def before_starting():
    for file in glob.glob("*.csv"):
        os.remove(file)
    
    for file in glob.glob("*.html"):
        os.remove(file)
    
    for file in glob.glob("*.jpg"):
        os.remove(file)

html_tables_for_query = []
CSV_DIR = "./"  
client = genai.Client(api_key="") 

def combine_csv_tables(csv_dir, max_files=1):
    combined_text = ""
    count = 0
    for filename in os.listdir(csv_dir):
        if filename.endswith(".csv"):
            if count >= max_files:
                break
            path = os.path.join(csv_dir, filename)
            try:
                df = pd.read_csv(path, on_bad_lines='skip') 
                combined_text += f"\nTable from {filename}:\n"
                combined_text += df.to_string(index=False)
                combined_text += "\n\n"
                count += 1
            except Exception as e:
                print(f"Skipping {filename} due to error: {e}")
    return combined_text


def ask_llama3_about_tables( table_text, user_query):
    prompt = f"""You are a helpful Data Analysis assistant. Below is table 
    which is given as a type of HTML table.
    You have to read this table and understand the data in it.
    Anaylze the table and answer the question based on the data in it.

    Take into account the following points:
    1. You have to read the tables and understand the data in it.
    2. You have to answer the question based on the data in it.
    3. You have need to keep in mind that if there are multiple tables answer the question only for the relevant table.

{table_text}

Answer the question based on the above data:
Question: {user_query}
Don't answer any uneccesary information, just answer the question.
Don't answer multiple times for the same question.
"""
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents = prompt
    )
    
    return response.text.split('\n')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins" : "*"}})


@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    user_query = data.get('query')
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    # table_text = combine_csv_tables(CSV_DIR, max_files=1)
    answer = ask_llama3_about_tables( html_tables_for_query, user_query)

    return jsonify({"answer": answer}), 200

@app.route('/processImage', methods=['POST'])
def process_image_route():
    before_starting()
    if 'image' not in request.files:
        return 'No file part', 400
    file = request.files['image']
    if file.filename == '':
        return 'No selected file', 400
    save_path = os.path.join('uploads', file.filename)
    file.save(save_path)
    extract_csv(save_path)
    detected_table_url = upload_image('detected_table.jpg')
    cropped_table_url = upload_image('cropped_table.jpg')
    table_structure_url = upload_image('table_structure.jpg')
    with open('output.csv', 'r') as file:
        csv_content = file.read()
    html_content = csv2html(csv_content)
    html_tables_for_query.append(html_content)
    return jsonify({"message": "Image processed successfully", "html_contents": [csv2html(csv_content)],
                    "csv_contents": [csv_content],
                    "detected_table_urls": [detected_table_url], 
                    "cropped_table_urls": [cropped_table_url], 
                    "table_structure_urls": [table_structure_url]}), 200

    
@app.route('/processPdf', methods=['POST'])
def process_pdf_route():
    # data = request.get_json()
    # pdf_path = data.get('pdf_path')

    html_tables_for_query.clear()
    before_starting()
    if 'pdf' not in request.files:
        return 'No file part', 400
    file = request.files['pdf']
    if file.filename == '':
        return 'No selected file', 400
    pdf_path = os.path.join('uploads', file.filename)
    file.save(pdf_path)

    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({"error": "Invalid PDF path"}), 400

    page_num, num_table = process_pdf(pdf_path)
    total_tables = combine()
    detected_table_urls = []
    for i in range(page_num):
        detected_table_url = upload_image(f"detected_table_{i}.jpg")
        detected_table_urls.append(detected_table_url)
    cropped_table_urls = []
    table_structure_urls = []
    for i in range(num_table):
        cropped_table_url = upload_image(f"cropped_table_{i}.jpg")
        table_structure_url = upload_image(f"table_structure_{i}.jpg")
        cropped_table_urls.append(cropped_table_url)
        table_structure_urls.append(table_structure_url)
    html_contents = []
    csv_contents = []
    for i in range(total_tables):
        with open(f"combined_group_{i+1}.csv", 'r') as file:
            csv_content = file.read()
        csv_contents.append(csv_content)
        html_content = csv2html(csv_content)
        html_contents.append(html_content)
    
    html_tables_for_query.append(html_contents)
    return jsonify({"message": "PDF processed successfully", "html_contents": html_contents, 
                    "csv_contents": csv_contents,
                    "detected_table_urls": detected_table_urls, 
                    "cropped_table_urls": cropped_table_urls, 
                    "table_structure_urls": table_structure_urls}), 200

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print(f"Server starting on port {port}...")
    app.run(host="0.0.0.0", port=port)
    print("Server exiting.")