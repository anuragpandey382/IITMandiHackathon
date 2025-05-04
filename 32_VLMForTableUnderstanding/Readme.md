# IITMandiHackathon
Dataset And Description

🧠 Summary of the Approach

This project implements a multi-stage processing pipeline for PDF and image analysis with web presentation:

PDF Upload and Image Extraction

Users upload a PDF via the web interface.

Each PDF page is programmatically rendered and broken into individual images for analysis.

Object Localization with taTr

Extracted page images are passed through a taTr model to detect and return bounding boxes of regions of interest.

Region Extraction and Enhancement

Detected bounding boxes are used to crop the original page images.

Each crop undergoes an enhancement step (e.g., contrast adjustment, denoising) to improve downstream processing accuracy.

Unitable Model Inference

Enhanced crops are fed into a fine-tuned Unitable model to perform the core analysis (e.g., classification, OCR, or other task-specific prediction).

Result Generation

Inference outputs are serialized into CSV and HTML files, saved under csv_final/ and html_final/ respectively.

Web Integration

The website dynamically reads from csv_final/ and html_final/ to present results via an interactive frontend.

⚙ Design Rationale and Techniques Used

Architecture & Frameworks

taTr Model: Chosen for its robust object localization performance on our target dataset.

Unitable Model: A fine-tuned architecture (e.g., CNN, Transformer, or hybrid) for the specific analysis task.

Libraries & Tools: PyTorch/TensorFlow, OpenCV for image processing, Pandas for CSV generation, Jinja2 (or similar) for HTML templating, Flask/React/Vue for the web frontend.

Key Components

Preprocessing:

Normalization of raw images.

Data augmentation (rotations, flips) during training to improve generalization.

Object Detection (taTr):

Multi-scale feature extraction to detect objects of varying sizes.

Non-maximum suppression to filter overlapping boxes.

Image Enhancement:

Contrast Limited Adaptive Histogram Equalization (CLAHE) or equivalent for contrast.

Gaussian denoising or other filters to reduce noise.

Unitable Inference:

Model architecture details: [layers, activation functions, normalization methods].

Training strategy: optimizer, learning rate schedule, regularization.

Result Serialization:

CSV: tabular format for bulk data processing.

HTML: human-readable reports with embedded images and metrics.

Web Frontend:

Dynamic data loading.

Interactive tables and charts (e.g., DataTables, Chart.js).

Rationale

Splitting localization and analysis improves modularity, allowing independent improvements.

Enhancement step boosts model accuracy by presenting cleaner inputs.

CSV + HTML outputs support both programmatic consumption and user-friendly display.

Final accuracy 55%
