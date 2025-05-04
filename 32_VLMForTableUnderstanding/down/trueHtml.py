import json
from collections import defaultdict
from pathlib import Path

# Define paths
train_dir = Path.home() / "acc" / "pubtabnet" / "train"
jsonl_path = Path.home() / "acc" / "pubtabnet" / "PubTabNet_2.0.0.jsonl"
output_base = Path.home() / "acc" / "pubtabnet" / "htmlPairsTest"

# Load JSONL into a dictionary
print("🔍 Indexing JSONL file...")
json_map = {}
with jsonl_path.open("r", encoding="utf-8") as f:
    for line in f:
        entry = json.loads(line)
        filename = entry.get("filename")
        if filename:
            json_map[filename] = entry

# OCR helper functions
def group_by_rows(ocr_data, y_threshold=10):
    rows = defaultdict(list)
    for cell in ocr_data:
        if 'bbox' not in cell:
            continue
        y = cell['bbox'][1]
        matched = False
        for key in rows:
            if abs(key - y) < y_threshold:
                rows[key].append(cell)
                matched = True
                break
        if not matched:
            rows[y].append(cell)
    return [sorted(row, key=lambda x: x['bbox'][0]) for key, row in sorted(rows.items())]

def extract_column_positions(rows, x_threshold=5):
    x_positions = []
    for row in rows:
        for cell in row:
            x = cell['bbox'][0]
            for known_x in x_positions:
                if abs(known_x - x) < x_threshold:
                    break
            else:
                x_positions.append(x)
    return sorted(x_positions)

def assign_cells_to_fixed_columns(row, col_positions, x_threshold=5):
    line = [""] * len(col_positions)
    for cell in row:
        x = cell['bbox'][0]
        for i, col_x in enumerate(col_positions):
            if abs(col_x - x) < x_threshold:
                text = "".join(cell.get('tokens', [])).strip()
                line[i] = text
                break
    return line

def collapse_into_empty_header_columns(table):
    num_cols = max(len(row) for row in table)
    for row in table:
        row += [""] * (num_cols - len(row))
    header_row = table[0]
    for i in range(1, len(table)):
        row = table[i]
        for j in range(num_cols):
            if row[j] == "":
                continue
            if j > 0 and row[j - 1] == "" and header_row[j] == "":
                row[j - 1] = row[j]
                row[j] = ""
            elif j < num_cols - 1 and row[j + 1] == "" and header_row[j] == "":
                row[j + 1] = row[j]
                row[j] = ""
    return table

def to_html(table):
    html = "<table border='1'>\n"
    for row in table:
        html += "  <tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>\n"
    html += "</table>"
    return html

# Get list of image names (as folder names) to process
image_names = [p.name for p in output_base.iterdir() if p.is_dir()]
print(f"📂 Will process {len(image_names)} selected image(s) from train set")

# Process each selected image
# for img_name in image_names:
#     print(f"\n🔧 Processing {img_name}...")

#     train_img_path = train_dir / img_name
#     if not train_img_path.exists():
#         print(f"⚠️  Image not found in train folder: {img_name}")
#         continue

#     entry = json_map.get(img_name)
#     if not entry:
#         print(f"⚠️  No matching JSON entry found for {img_name}")
#         continue

#     try:
#         ocr_data = entry['html']['cells']
#         grouped_rows = group_by_rows(ocr_data)
#         column_positions = extract_column_positions(grouped_rows)
#         table = [assign_cells_to_fixed_columns(row, column_positions) for row in grouped_rows]
#         table = collapse_into_empty_header_columns(table)
#         html_output = to_html(table)

#         # Save HTML to htmlPairsTest/[img_name]/true.html
#         out_path = output_base / img_name / "true.html"
#         out_path.parent.mkdir(parents=True, exist_ok=True)

#         with out_path.open("w", encoding="utf-8") as f:
#             f.write(html_output)

#         print(f"✅ Saved HTML to {out_path}")
#     except Exception as e:
#         print(f"❌ Error processing {img_name}: {e}")

for img_name in image_names:
    print(f"\n🔧 Processing {img_name}...")

    # Ensure filename ends with .png
    img_filename = img_name if img_name.endswith(".png") else img_name + ".png"

    train_img_path = train_dir / img_filename
    if not train_img_path.exists():
        print(f"⚠️  Image not found in train folder: {img_filename}")
        continue

    entry = json_map.get(img_filename)
    if not entry:
        print(f"⚠️  No matching JSON entry found for {img_filename}")
        continue
 
    try:
        ocr_data = entry['html']['cells']
        grouped_rows = group_by_rows(ocr_data)
        column_positions = extract_column_positions(grouped_rows)
        table = [assign_cells_to_fixed_columns(row, column_positions) for row in grouped_rows]
        table = collapse_into_empty_header_columns(table)
        html_output = to_html(table)
        # Save HTML to htmlPairsTest/[img_name]/true.html
        out_path = output_base / img_name / "true.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            f.write(html_output)
        print(f"✅ Saved HTML to {out_path}")
    except Exception as e:
        print(f"❌ Error processing {img_name}: {e}")
