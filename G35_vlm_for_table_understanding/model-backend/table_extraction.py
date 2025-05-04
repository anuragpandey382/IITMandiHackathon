import os
import torch
from transformers import AutoModelForObjectDetection, TableTransformerForObjectDetection
from torchvision import transforms
from PIL import Image, ImageDraw
from pdf2image import convert_from_path
import numpy as np
import easyocr
import pandas as pd
from tqdm import tqdm
from extract_table import visualize_detected_tables

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

table_detector = AutoModelForObjectDetection.from_pretrained(
    "microsoft/table-transformer-detection", revision="no_timm"
).to(device)

structure_recognizer = TableTransformerForObjectDetection.from_pretrained(
    "microsoft/table-structure-recognition-v1.1-all"
).to(device)

class MaxResize:
    def __init__(self, max_size=1000):
        self.max_size = max_size

    def __call__(self, image):
        width, height = image.size
        scale = self.max_size / max(width, height)
        new_size = (int(width * scale), int(height * scale))
        return image.resize(new_size, Image.Resampling.LANCZOS)

detection_transform = transforms.Compose([
    MaxResize(800),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

structure_transform = transforms.Compose([
    MaxResize(1000),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

def box_cxcywh_to_xyxy(x):
    x_c, y_c, w, h = x.unbind(-1)
    b = [(x_c - 0.5 * w), (y_c - 0.5 * h),
         (x_c + 0.5 * w), (y_c + 0.5 * h)]
    return torch.stack(b, dim=1)

def rescale_bboxes(out_bbox, size):
    img_w, img_h = size
    b = box_cxcywh_to_xyxy(out_bbox)
    b = b * torch.tensor([img_w, img_h, img_w, img_h],
                         dtype=torch.float32)
    return b

def outputs_to_objects(outputs, img_size, id2label):
    m = outputs.logits.softmax(-1).max(-1)
    pred_labels = list(m.indices.detach().cpu().numpy())[0]
    pred_scores = list(m.values.detach().cpu().numpy())[0]
    pred_bboxes = outputs['pred_boxes'].detach().cpu()[0]
    pred_bboxes = [elem.tolist() for elem in rescale_bboxes(pred_bboxes, img_size)]

    objects = []
    for label, score, bbox in zip(pred_labels, pred_scores, pred_bboxes):
        class_label = id2label.get(int(label), 'no object')
        if class_label != 'no object':
            objects.append({'label': class_label, 'score': float(score),
                            'bbox': [float(elem) for elem in bbox]})
    return objects

def get_cell_coordinates_by_row(table_data):
    rows = [entry for entry in table_data if entry['label'] == 'table row']
    columns = [entry for entry in table_data if entry['label'] == 'table column']

    rows.sort(key=lambda x: x['bbox'][1])
    columns.sort(key=lambda x: x['bbox'][0])

    cell_coordinates = []

    for row in rows:
        row_cells = []
        for column in columns:
            cell_bbox = [column['bbox'][0], row['bbox'][1],
                         column['bbox'][2], row['bbox'][3]]
            row_cells.append({'column': column['bbox'], 'cell': cell_bbox})

        row_cells.sort(key=lambda x: x['column'][0])
        cell_coordinates.append({'row': row['bbox'], 'cells': row_cells,
                                 'cell_count': len(row_cells)})

    cell_coordinates.sort(key=lambda x: x['row'][1])
    return cell_coordinates

def apply_ocr(cell_coordinates, cropped_table, reader):
    data = dict()
    max_num_columns = 0
    for idx, row in enumerate(cell_coordinates):
        row_text = []
        for cell in row["cells"]:
            cell_image = np.array(cropped_table.crop(cell["cell"]))
            result = reader.readtext(cell_image)
            text = " ".join([x[1] for x in result]) if result else ""
            row_text.append(text)

        if len(row_text) > max_num_columns:
            max_num_columns = len(row_text)

        data[idx] = row_text

    for row, row_data in data.copy().items():
        if len(row_data) != max_num_columns:
            row_data += [""] * (max_num_columns - len(row_data))
        data[row] = row_data

    return data

def process_pdf(pdf_path):
    # if not os.path.exists(output_dir):
    #     os.makedirs(output_dir)

    pages = convert_from_path(pdf_path, dpi=300, poppler_path=r"C:\poppler-24.08.0\Library\bin")

    reader = easyocr.Reader(['en'])
    num_tables = 0
    for page_num, image in enumerate(tqdm(pages, desc="Processing pages")):

        pixel_values = detection_transform(image).unsqueeze(0).to(device)
        with torch.no_grad():
            outputs = table_detector(pixel_values)

        id2label = table_detector.config.id2label
        id2label[len(id2label)] = "no object"
        objects = outputs_to_objects(outputs, image.size, id2label)                                                             
        fig = visualize_detected_tables(image, objects, f'detected_table_{page_num}.jpg')

        for idx, obj in enumerate(objects):
            bbox = obj['bbox']
            cropped_table = image.crop(bbox).convert("RGB")
            cropped_table.save(f"cropped_table_{num_tables}.jpg")

            pixel_values = structure_transform(cropped_table).unsqueeze(0).to(device)
            with torch.no_grad():
                outputs = structure_recognizer(pixel_values)

            structure_id2label = structure_recognizer.config.id2label
            structure_id2label[len(structure_id2label)] = "no object"
            cells = outputs_to_objects(outputs, cropped_table.size, structure_id2label)

            cropped_table_visualized = cropped_table.copy()
            draw = ImageDraw.Draw(cropped_table_visualized)

            for cell in cells:
                draw.rectangle(cell["bbox"], outline="red")

            cropped_table_visualized.save(f"table_structure_{num_tables}.jpg")
            num_tables += 1

            cell_coordinates = get_cell_coordinates_by_row(cells)
            data = apply_ocr(cell_coordinates, cropped_table, reader)

            # Save to CSV
            csv_filename = f"page_{page_num+1}_table_{idx+1}.csv"
            csv_path = csv_filename
            with open(csv_path, 'w', encoding='utf-8') as f:
                for row in data.values():
                    f.write(','.join(row) + '\n')

            print(f"Saved table to {csv_path}")
    return page_num+1, num_tables

# pdf_path = "ca-warn-report.pdf"
# output_dir = "extracted_tables"
# process_pdf(pdf_path, output_dir)
