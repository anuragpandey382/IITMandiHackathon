from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

CSV_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csv_final')
HTML_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'html_final')

# ✅ Define these sets at the top level
sent_csv_files = set()
sent_html_files = set()

@app.route('/new-data', methods=['GET'])
def send_new_files():
    global sent_csv_files, sent_html_files  # <- Access global sets

    new_data = {
        'csv_files': [],
        'html_files': []
    }

    # Process new CSV files
    for filename in os.listdir(CSV_FOLDER):
        if filename.endswith('.csv') and filename not in sent_csv_files:
            filepath = os.path.join(CSV_FOLDER, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            new_data['csv_files'].append({'filename': filename, 'content': content})
            sent_csv_files.add(filename)

    # Process new HTML files
    for filename in os.listdir(HTML_FOLDER):
        if filename.endswith('.html') and filename not in sent_html_files:
            filepath = os.path.join(HTML_FOLDER, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            new_data['html_files'].append({'filename': filename, 'content': content})
            sent_html_files.add(filename)

    return jsonify(new_data), 200

if __name__ == '__main__':
    os.makedirs(CSV_FOLDER, exist_ok=True)
    os.makedirs(HTML_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=8050)
