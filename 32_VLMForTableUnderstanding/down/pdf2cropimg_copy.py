import os
import time
import re
import shutil
import subprocess
from pathlib import Path
import pytesseract

import torch
import cv2
from PIL import Image
from pdf2image import convert_from_path
from transformers import TableTransformerForObjectDetection, AutoImageProcessor

import cv2
import numpy as np

from PIL import Image
import re
import os

# === Config ===
WATCH_DIR = Path("/home/teaching/Desktop/test/down/upload")
OUTPUT_DIR = Path("output")
CROPPED_DIR = Path("cropped_tables")
ENHANCED_DIR = Path("enhanced")
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

# === Setup ===
OUTPUT_DIR.mkdir(exist_ok=True)
CROPPED_DIR.mkdir(exist_ok=True)
ENHANCED_DIR.mkdir(exist_ok=True)
WATCH_DIR.mkdir(exist_ok=True)

# === Load model once ===
model = TableTransformerForObjectDetection.from_pretrained("microsoft/table-transformer-detection")
processor = AutoImageProcessor.from_pretrained("microsoft/table-transformer-detection")

# === Functions ===

def convert_to_pdf(input_path: Path, output_dir: Path) -> Path:
    subprocess.run([
        'soffice', '--headless',
        '--convert-to', 'pdf',
        '--outdir', str(output_dir),
        str(input_path)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    pdf_file = output_dir / (input_path.stem + '.pdf')
    if not pdf_file.exists():
        raise FileNotFoundError(f"Failed to convert {input_path} to PDF")
    return pdf_file

def pdf_to_images(pdf_path: Path, output_dir: Path, dpi: int = 200):
    pages = convert_from_path(str(pdf_path), dpi=dpi)
    pad_length = len(str(len(pages)))
    for i, page in enumerate(pages, start=1):
        img_path = output_dir / f"{pdf_path.stem}_page{str(i).zfill(pad_length)}.png"
        page.save(img_path, 'PNG')
        print(f"→ {img_path.name}")

def convert_any(input_file: str, outdir: str = 'output'):
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    if CROPPED_DIR.exists():
        shutil.rmtree(CROPPED_DIR)
    if ENHANCED_DIR.exists():
        shutil.rmtree(ENHANCED_DIR)

    OUTPUT_DIR.mkdir(exist_ok=True)
    CROPPED_DIR.mkdir(exist_ok=True)
    ENHANCED_DIR.mkdir(exist_ok=True)

    input_path = Path(input_file)
    output_dir = Path(outdir)
    ext = input_path.suffix.lower()

    if ext in IMAGE_EXTS:
        shutil.copy(input_path, output_dir / input_path.name)
        print(f"[COPIED] {input_path.name}")
        return

    temp_pdf = None
    if ext != '.pdf':
        print(f"[STEP 1] Converting {input_path.name} → PDF…")
        temp_pdf = convert_to_pdf(input_path, output_dir)
        pdf_path = temp_pdf
    else:
        pdf_path = input_path

    print(f"[STEP 2] Converting {pdf_path.name} → PNG…")
    pdf_to_images(pdf_path, output_dir)

    if temp_pdf and temp_pdf.exists():
        os.remove(temp_pdf)
        print(f"[CLEANUP] Removed: {temp_pdf.name}")

    print("[DONE: CONVERSION]")

def detect_tables():
    def sorted_nicely(file_list):
        return sorted(file_list, key=lambda x: [int(t) if t.isdigit() else t.lower() for t in re.split('([0-9]+)', x)])

    image_files = sorted_nicely([
        f for f in os.listdir(OUTPUT_DIR)
        if any(f.lower().endswith(ext) for ext in IMAGE_EXTS)
    ])

    for filename in image_files:
        image_path = OUTPUT_DIR / filename
        image = Image.open(image_path).convert("RGB")

        encoding = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**encoding)

        target_sizes = torch.tensor([image.size[::-1]])
        results = processor.post_process_object_detection(outputs, threshold=0.91, target_sizes=target_sizes)[0]

        if len(results["boxes"]) == 0:
            print(f"[INFO] No tables in {filename}")
            continue

        for idx, box in enumerate(results["boxes"]):
            x0, y0, x1, y1 = [int(round(v)) for v in box.tolist()]
            cropped = image.crop((x0, y0, x1, y1))
            crop_name = f"{Path(filename).stem}_table{idx+1:02d}.jpg"
            cropped.save(CROPPED_DIR / crop_name)

        print(f"[CROPPED] {len(results['boxes'])} table(s) from {filename}")

def enhance_images():
    def sorted_nicely(file_list):
        return sorted(file_list, key=lambda x: [int(t) if t.isdigit() else t.lower() for t in re.split('([0-9]+)', x)])

    image_files = sorted_nicely([
        f for f in os.listdir(CROPPED_DIR)
        if any(f.lower().endswith(ext) for ext in IMAGE_EXTS)
    ])

    for filename in image_files:
        input_path = CROPPED_DIR / filename
        output_path = ENHANCED_DIR / filename

        image = cv2.imread(str(input_path))
        if image is None:
            print(f"[WARN] Failed to load {filename}")
            continue

        enhanced = cv2.detailEnhance(image, sigma_s=10, sigma_r=0.15)
        cv2.imwrite(str(output_path), enhanced)
        
        print(f"[ENHANCED] {filename}")


def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image from {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
    return img, denoised

def extract_table_features(image_path):
    original_img, processed_img = preprocess_image(image_path)
    pil_img = Image.fromarray(processed_img)
    text = pytesseract.image_to_string(pil_img)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    edges = cv2.Canny(processed_img, 50, 150, apertureSize=3)
    lines_p = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100,
                              minLineLength=original_img.shape[1] // 3, maxLineGap=20)
    horizontal_lines = []
    if lines_p is not None:
        for line in lines_p:
            x1, y1, x2, y2 = line[0]
            if abs(y2 - y1) < 10 and abs(x2 - x1) > original_img.shape[1] // 3:
                horizontal_lines.append((min(y1, y2), min(x1, x2), max(x1, x2)))
    column_separators = []
    for line in lines:
        spaces = [m.start() for m in re.finditer(r'\s{3,}', line)]
        pipes = [m.start() for m in re.finditer(r'\|', line)]
        if pipes:
            column_separators.append(len(pipes) + 1)
        elif spaces:
            column_separators.append(len(spaces) + 1)
    estimated_columns = max(set(column_separators), key=column_separators.count) if column_separators else 0
    data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
    text_blocks = [word for word in data['text'] if word.strip()]
    height, width = original_img.shape[:2]
    headers = []
    if lines and len(lines) > 1:
        for line in lines:
            if line.strip():
                headers = re.split(r'\s{3,}|\|', line)
                headers = [h.strip() for h in headers if h.strip()]
                break
    return {
        "estimated_columns": estimated_columns if estimated_columns > 0 else (len(headers) if headers else 3),
        "estimated_rows": len(horizontal_lines) if horizontal_lines else len(lines),
        "table_width": width,
        "table_height": height,
        "text_blocks": len(text_blocks),
        "headers": headers,
        "text_sample": text[:300]
    }

def detect_column_structure(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    patterns = []
    for line in lines[:10]:
        spaces = [m.start() for m in re.finditer(r'\s{3,}', line)]
        pipes = [m.start() for m in re.finditer(r'\|', line)]
        if pipes:
            patterns.append(pipes)
        elif spaces:
            patterns.append(spaces)
    if patterns and len(patterns) >= 2:
        pattern_lengths = [len(p) for p in patterns]
        if max(pattern_lengths) - min(pattern_lengths) <= 1:
            return max(set(pattern_lengths), key=pattern_lengths.count) + 1
    return 0

def compare_tables(img1_path, img2_path):
    try:
        table1 = extract_table_features(img1_path)
        table2 = extract_table_features(img2_path)
        text1 = pytesseract.image_to_string(Image.open(img1_path))
        text2 = pytesseract.image_to_string(Image.open(img2_path))
        cols1 = detect_column_structure(text1)
        cols2 = detect_column_structure(text2)
        if cols1 > 0 and cols2 > 0:
            table1["detected_columns"] = cols1
            table2["detected_columns"] = cols2
        columns_match = False
        if "detected_columns" in table1 and "detected_columns" in table2:
            columns_match = table1["detected_columns"] == table2["detected_columns"]
        else:
            columns_match = abs(table1["estimated_columns"] - table2["estimated_columns"]) <= 1
        width_ratio = table1["table_width"] / table2["table_width"] if table2["table_width"] > 0 else 0
        width_similar = 0.7 <= width_ratio <= 1.3
        header_consistent = True
        continuation_keywords = ["Model efficiency", "Report and code quality", "Real-time Deployment"]
        text_suggests_continuation = any(keyword in text2 for keyword in continuation_keywords)
        evaluation_continuation = "Report and code quality" in text2 and "F1 scores" in text1
        is_same_table = (columns_match and width_similar) or evaluation_continuation or text_suggests_continuation
        return {"result": is_same_table}
    except Exception as e:
        return {"result": False, "reason": f"Error during comparison: {str(e)}"}

def analyze_table_content(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        evaluation_keywords = [
            "Model Accuracy", "F1 scores", "Confusion matrix",
            "Model efficiency", "Report and code quality", "Embedding",
            "Preprocessing", "Real-time", "Deployment", "Weightage"
        ]
        matches = [keyword for keyword in evaluation_keywords if keyword in text]
        part1_keywords = ["Model Accuracy", "F1 scores", "Confusion matrix"]
        part2_keywords = ["Report and code quality", "Embedding", "Real-time Deployment"]
        is_part1 = any(keyword in text for keyword in part1_keywords)
        is_part2 = any(keyword in text for keyword in part2_keywords)
        return {
            "is_evaluation_table": len(matches) > 1,
            "is_part1": is_part1,
            "is_part2": is_part2,
            "matching_keywords": matches
        }
    except Exception as e:
        return {"error": str(e)}

def main(image1_path, image2_path):
    analysis1 = analyze_table_content(image1_path)
    analysis2 = analyze_table_content(image2_path)
    if (not "error" in analysis1 and not "error" in analysis2 and
        analysis1.get("is_evaluation_table", False) and
        analysis2.get("is_evaluation_table", False) and
        analysis1.get("is_part1", False) and analysis2.get("is_part2", False)):
        return True
    result = compare_tables(image1_path, image2_path)
    return result["result"]

# ----------------------------- [Main Wrapper Function] ----------------------------- #
image_folder='enhanced'
pair_folder='pair'
def detect_table_continuations():
    continuation_pairs = []
    os.makedirs(pair_folder, exist_ok=True)
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

    paired_file_path = os.path.join(pair_folder, 'paired.txt')

    def extract_page_number(filename):
        match = re.search(r'page(\d+)', filename, re.IGNORECASE)
        return int(match.group(1)) if match else -1

    image_files = [
        f for f in os.listdir(image_folder)
        if any(f.lower().endswith(ext) for ext in image_extensions)
    ]
    image_pages = [(f, extract_page_number(f)) for f in image_files if extract_page_number(f) != -1]
    image_pages.sort(key=lambda x: x[1])

    if len(image_pages) < 2:
        # Not enough files to compare, but still create paired.txt
        with open(paired_file_path, 'w') as f:
            pass
        print("Less than 2 valid image pages. Created empty paired.txt.")
        return continuation_pairs

    for i in range(len(image_pages) - 1):
        file1, page1 = image_pages[i]
        file2, page2 = image_pages[i + 1]
        if page2 - page1 == 1:
            img1 = os.path.join(image_folder, file1)
            img2 = os.path.join(image_folder, file2)
            if main(img1, img2):
                continuation_pairs.append((file1, file2))

    # Always write paired.txt
    with open(paired_file_path, 'w') as f:
        for file1, file2 in continuation_pairs:
            name1 = os.path.splitext(file1)[0]
            name2 = os.path.splitext(file2)[0]
            f.write(f"{name1} {name2}\n")

    if continuation_pairs:
        print("\nDetected continuation pairs:")
        for pair in continuation_pairs:
            print(pair)
    else:
        print("No continuation pairs detected. Created empty paired.txt.")

    return continuation_pairs


def is_supported(file: Path):
    return file.suffix.lower() in IMAGE_EXTS.union({'.pdf', '.docx', '.pptx'})

def watch_and_process():
    print(f"👀 Watching folder: {WATCH_DIR}")
    seen = set()

    while True:
        for file in WATCH_DIR.iterdir():
            if file.is_file() and file.name not in seen and is_supported(file):
                print(f"\n[NEW FILE] {file.name}")
                try:
                    convert_any(str(file))
                    detect_tables()
                    enhance_images()
                    detect_table_continuations()
                      # DELETE the uploaded file when done
                    file.unlink()
                    print(f"[DONE + DELETED] {file.name}")
                except Exception as e:
                    print(f"[ERROR] processing {file.name}: {e}")
        time.sleep(5)

# === Run watcher ===
if __name__ == "__main__":
    watch_and_process()
