import os
import requests
import cv2
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
dataset_dir = "image_dataset"
output_base_dir = "image_results"
os.makedirs(output_base_dir, exist_ok=True)

API_URL = "http://localhost:8000/analyze_tongue"  # FastAPI server URL
results = []

for filename in os.listdir(dataset_dir):
    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    image_path = os.path.join(dataset_dir, filename)
    try:
        logger.info(f"Sending {filename} to server...")

        # Send request to FastAPI server
        with open(image_path, "rb") as img_file:
            response = requests.post(API_URL, files={"file": (filename, img_file, "image/jpeg")})

        if response.status_code != 200:
            logger.warning(f"Server returned error for {filename}: {response.status_code} - {response.text}")
            continue

        data = response.json()

        # Save segmented image to subfolder
        segmented_path = data["segmented_image_path"]
        subfolder = os.path.join(output_base_dir, os.path.splitext(filename)[0])
        os.makedirs(subfolder, exist_ok=True)

        # Download segmented image (optional: only if needed)
        # shutil.copy(segmented_path, os.path.join(subfolder, "segmented.jpg"))

        # Save composite results
        score_data = {
            "image": filename,
            "white_coating_%": data["white_coating"]["white_coating_percentage"],
            "avg_redness": data["papillae_analysis"]["avg_redness"],
            "avg_size": data["papillae_analysis"]["avg_size"],
            "crack_score": data["Cracks"]["score"],
            "jagged_score": data["Jaggedness"],
            "Nutrition_Score": data["NutritionScore"],
            "Mantle_Score": data["MantleScore"]
        }
        results.append(score_data)

        # Write scores to a text file
        score_text_path = os.path.join(subfolder, "scores.txt")
        with open(score_text_path, "w") as f:
            for key, value in score_data.items():
                f.write(f"{key}: {value}\n")

    except Exception as e:
        logger.error(f"Failed to process {filename}: {str(e)}")

# Save all results to CSV
csv_path = os.path.join(output_base_dir, "results.csv")
pd.DataFrame(results).to_csv(csv_path, index=False)
logger.info(f"Evaluation complete. Results saved to {csv_path}")
