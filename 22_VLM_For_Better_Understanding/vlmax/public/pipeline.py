# ----------IMPORTS----------
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
from bs4 import BeautifulSoup
import json
import csv
import os
import hashlib
import argparse
from pathlib import Path
import torch
import matplotlib.pyplot as plt
from transformers import AutoImageProcessor, TableTransformerForObjectDetection, DetrFeatureExtractor
from pdf2image import convert_from_path

# -----------------------------

results = {"img_path": [], "file_path": []}

final = {}


device = "cuda" if torch.cuda.is_available() else "cpu"
MODEL = "./pix2struct-base-table2html"
processor = AutoProcessor.from_pretrained(MODEL)
model = AutoModelForImageTextToText.from_pretrained(MODEL)
model.to(device)
model.eval()

dir = './public/results/'
def inference(image):
    encoding = processor(image, return_tensors="pt", max_patches=1024)
    with torch.inference_mode():
        flattened_patches = encoding.pop("flattened_patches").to(device)
        attention_mask = encoding.pop("attention_mask").to(device)
        predictions = model.generate(flattened_patches=flattened_patches, attention_mask=attention_mask, max_new_tokens=1024)

    predictions_decoded = processor.tokenizer.batch_decode(predictions, skip_special_tokens=True)

    html_code = predictions_decoded[0]
    return html_code

# --------SAVING DATA----------
def save(html_code, key):
    os.makedirs(dir, exist_ok=True)
    base_name = hashlib.sha256(html_code.encode()).hexdigest()[:8]
    print(base_name)
    key = key.split('.')[0]
    if key not in final:
        final[key] = {}
    
    
    final[key]['csv'] = (os.path.join("./results", f'{base_name}.csv'))
    final[key]['html'] = (os.path.join("./results", f'{base_name}.html'))
    with open(os.path.join(dir, f'{base_name}.html'), 'w', encoding='utf-8') as f:
        f.write(html_code)

    soup = BeautifulSoup(html_code, 'html.parser')
    table = soup.find('table')
    rows = table.find_all('tr')

    with open(os.path.join(dir, f'{base_name}.csv'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for row in rows:
            cols = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
            writer.writerow(cols)
# ------------------------------

# Visualization colors
COLORS = [[0.000, 0.447, 0.741], [0.850, 0.325, 0.098], [0.929, 0.694, 0.125],
          [0.494, 0.184, 0.556], [0.466, 0.674, 0.188], [0.301, 0.745, 0.933]]

def plot_results(image, scores, labels, boxes, model, save_path):
    plt.figure(figsize=(16, 10))
    plt.imshow(image)
    ax = plt.gca()
    colors = COLORS * 100
    for score, label, (xmin, ymin, xmax, ymax), color in zip(scores.tolist(), labels.tolist(), boxes.tolist(), colors):
        ax.add_patch(plt.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin, fill=False, color=color, linewidth=3))
        text = f'{model.config.id2label[label]}: {score:.2f}'
        ax.text(xmin, ymin, text, fontsize=12, bbox=dict(facecolor='yellow', alpha=0.5))
    plt.axis('off')
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print(f"Saved: {save_path}")

def detect_and_crop_tables(image, base_name, page_num, save_dir, margin=10):
    processor = AutoImageProcessor.from_pretrained("microsoft/table-transformer-detection")
    model = TableTransformerForObjectDetection.from_pretrained("microsoft/table-transformer-detection")

    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)

    target_sizes = torch.tensor([image.size[::-1]])
    results = processor.post_process_object_detection(outputs, threshold=0.98, target_sizes=target_sizes)[0]

    if len(results["boxes"]) == 0:
        print(f"No tables found on page {page_num}")
        return []

    vis_path = save_dir / f"{base_name}_page_{page_num}_boxes.png"
    plot_results(image, results["scores"], results["labels"], results["boxes"], model, vis_path)

    table_paths = []
    for idx, (score, label, box) in enumerate(zip(results["scores"], results["labels"], results["boxes"])):
        if model.config.id2label[label.item()] == "table":
            xmin, ymin, xmax, ymax = map(int, box.tolist())
            # Add margin while staying within image bounds
            xmin = max(xmin - margin-15 , 0)
            ymin = max(ymin - margin, 0)
            xmax = min(xmax + margin+15 , image.width)
            ymax = min(ymax + margin, image.height)
            cropped = image.crop((xmin, ymin, xmax, ymax))
            crop_path = save_dir / f"{base_name}_page_{page_num}_table_{idx+1}.png"
            cropped.save(crop_path)
            print(f"Saved cropped table: {crop_path}")
            table_paths.append(crop_path)

    return table_paths

def structure_recognition(image_paths, save_dir):
    model = TableTransformerForObjectDetection.from_pretrained(
        "microsoft/table-transformer-structure-recognition", device_map="auto"
    )
    feature_extractor = DetrFeatureExtractor()
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model.to(device)

    for path in image_paths:
        image = Image.open(path).convert("RGB")
        encoding = feature_extractor(image, return_tensors="pt")
        encoding = {k: v.to(device) for k, v in encoding.items()}

        with torch.no_grad():
            outputs = model(**encoding)

        target_sizes = [image.size[::-1]]
        results = feature_extractor.post_process_object_detection(outputs, threshold=0.6, target_sizes=target_sizes)[0]

        structure_path = save_dir / f"{path.stem}_structure.png"
        plot_results(image, results['scores'], results['labels'], results['boxes'], model, structure_path)

def process_pdf(pdf_path, save_dir):
    pages = convert_from_path(pdf_path)
    base_name = pdf_path.stem
    for i, image in enumerate(pages, start=1):
        print(f"\nProcessing page {i}...")
        tables = detect_and_crop_tables(image, base_name, i, save_dir)
        if tables:
            structure_recognition(tables, save_dir)

def process_image(image_path, save_dir):
    image = Image.open(image_path).convert("RGB")
    base_name = image_path.stem
    tables = detect_and_crop_tables(image, base_name, 1, save_dir)
    if tables:
        structure_recognition(tables, save_dir)

pics = {"pics": []}
def load_images():
    for file in os.walk("./public/preprocess_results/"):
        for name in file[2]:
            names = name.split('_')
            if(len(names) < 5): 
                continue
            pageNo = name.split('_')[2]
            tableNo = name.split('_')[4]
            key = f"page_{pageNo}_table_{tableNo}"
            key = key.split('.')[0]
            if key not in final:
                final[key] = {}

            if not (name.endswith('structure.png') or name.endswith('boxes.png')):
                final[key]['main'] = (os.path.join('./preprocess_results/', name))
                image_path = os.path.join(file[0], name)
                print(image_path)
                image = Image.open(image_path).convert("RGB")
                html_code = inference(image)
                save(html_code, key)
            elif (name.endswith('structure.png')):
                if key not in final:
                    final[key] = {}
                final[key]['struct'] = os.path.join('/preprocess_results/', name)
            
            final[key]['boxes'] = os.path.join('/preprocess_results/', '_'.join(names[:3]) + '_boxes.png')



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect tables in PDFs or images.")
    parser.add_argument("input_file", type=str, help="Path to input PDF or image")
    args = parser.parse_args()

    input_path = Path(args.input_file).resolve()
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        exit(1)

    results_dir = Path.cwd() / "public/preprocess_results/"
    results_dir.mkdir(exist_ok=True)

    if input_path.suffix.lower() == ".pdf":
        process_pdf(input_path, results_dir)
    elif input_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
        process_image(input_path, results_dir)
    else:
        print("Unsupported file type. Use a PDF or image file.")

    load_images()

    with open('public/results.json', 'w') as f:
        json.dump(final, f, indent=4)
    
    data = ""
    for file in os.listdir("./public/results/"):
        if file.endswith('.html'):
            with open(os.path.join("./public/results/", file), 'r', encoding='utf-8') as f:
                data += f.read()
    
    with open('public/results.html', 'w') as f:
        f.write(data)
    print("All files processed and saved.")


    

