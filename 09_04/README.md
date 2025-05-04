# DeepTabNet
## Architechtural Diagram
![Image](https://github.com/user-attachments/assets/140f2e1f-8758-49db-941c-4db8e19c829c)
![Image](https://github.com/user-attachments/assets/a20c9963-3779-49fb-a13b-914fb199f52f)
## Project Overview

1. Table Detection with YOLOv8
  Dataset Preparation
   >Curated a subset of the PubLayNet dataset, filtering for table structures across diverse document types (scanned PDFs,digital reports).
   >Annotated tables with high-precision bounding boxes, including edge cases like rotated tables, nested layouts, and low-resolution scans.

  Model Training
  >Fine-tuned YOLOv8m (medium variant) using transfer learning, optimizing anchor boxes for common table aspect ratios.
  >Augmented training data with affine transformations (rotation, scaling, shear) to improve robustness.

  Performance
  >Achieved 98.98% precision, 99.10% recall, and 99.3 mAP50 on a held-out test set, with consistent performance across document domains.

2. Cell-Level OCR Extraction with PaddleOCR
  Preprocessing
    >Cropped document regions using YOLOv8’s table bounding boxes.
    >Cell Detection & Text Recognition
    >Leveraged PaddleOCR’s layout analysis module to segment individual cells within each table, generating coordinates for all four cell boundaries.

3. Structured Reconstruction with Llama 4 Scout
    >Spatial-Aware Table Parsing
    >Designed a coordinate-based prompt for Llama 4 Scout, instructing the model to:
      >Infer row/column alignment using cell bounding box positions.
      >Identify headers by analyzing text patterns (e.g., bolded cells, positional consistency).
      >Output data in a JSON schema mirroring the table’s logical structure.

Validation & Conversion.
To ensure robustness, we rigorously tested our pipeline on diverse and challenging datasets and we are getting accurate results.
Developed a Python utility to transform validated JSON into CSV, handling edge cases like empty cells or multi-line text.

## Design Rationale and Techniques Used


🎯 Design Rationale

The design is modular and separates concerns into three key stages:

Document Preprocessing
Converts PDFs to images if needed, so the pipeline can work uniformly on image inputs.

Table Detection
Detects table regions in images using a YOLOv8 model trained on a custom table dataset for accurate and domain-specific detection performance.

Text Recognition and Structuring
Performs OCR to extract text along with their bounding boxes from the detected tables. This spatial information helps in reconstructing structured tables.

Output Generation
Saves the processed results in JSON and CSV formats, with optional cropped table images for review or debugging.

🛠 Techniques Used
1. PDF to Image Conversion
Library: PyMuPDF (fitz)
Purpose: Converts each page of a PDF to PNG for downstream processing.
File: main.py
Function: convert_pdf_to_pngs()

2. Table Detection
Library: ultralytics
Model: YOLOv8, trained on a custom dataset of tables
File: utils.py
Function: detect_tables()
Technique: Returns bounding boxes for detected table regions in input images.

3. Text Recognition and Structuring
Library: PaddleOCR
Files: utils.py
Class: TextRecognizer
Technique:Performs OCR on each detected table region.
Extracts both the text and their respective bounding box coordinates.
This spatial context is used to reconstruct tabular structure accurately.

4. Data Structuring Using LLM
Service: Together API
Model: meta-llama/Llama-4-Scout-17B-16E-Instruct
File: helper.py
Technique:Sends the cropped table image and bounding box text pairs to the LLM.
The model returns a structured JSON object representing table headers and rows.

5. Output Creation
Format: JSON and CSV
File: utils.py
Functions:
create_csv() – converts structured data into a CSV
save_cropped_table_image() – crops and saves images of detected tables
encode_image() – base64-encodes images for LLM input

## Results and Evaluation
![Image](https://github.com/user-attachments/assets/ffb3b29d-c626-45c9-8414-7107922ae179)
![Image](https://github.com/user-attachments/assets/b191c93d-bde0-4741-bdf2-48de7dd43eaf)
![Image](https://github.com/user-attachments/assets/6e378582-937b-4ae8-bbd1-bf1105dadaa7)
#### Evaluation
![Image](https://github.com/user-attachments/assets/9b1b97f4-4611-401b-b765-560780bdac4e)
![Image](https://github.com/user-attachments/assets/5137934d-d383-43b4-ba93-c4e3827dbbe2)
![Image](https://github.com/user-attachments/assets/549a3ded-fcbf-47db-b344-343effbde3ba)
![Image](https://github.com/user-attachments/assets/f269df49-3e33-48a2-ba12-4fcfa1fed172)
