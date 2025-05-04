import torch
import numpy as np
import cv2
from segment_anything import sam_model_registry, SamPredictor

from inference_sdk import InferenceHTTPClient
import cv2

# Load image
image = cv2.imread('tongue3.png')

# Create client
CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="UySFJBcSCBCxmwiEA9ea"
)

result = CLIENT.infer(image, model_id="tongue-93kco/3")

if "predictions" in result and len(result["predictions"]) > 0:
    prediction = result["predictions"][0]
    x = prediction["x"]
    y = prediction["y"]
    print(f"Detected bounding box center: x = {x}, y = {y}")
    input_point = np.array([[x, y]])
else:
    print("❌ No predictions found. Exiting.")
    exit()

input_label = np.array([1])  # 1 = positive label for tongue point


# === USER SETTINGS ===
image_path = "tongue3.png"  # Your input image filename (place in same folder)
output_path = "tongue_output.jpg"  # Output filename
sam_checkpoint = "sam_vit_h.pth"  # Path to downloaded SAM model checkpoint
model_type = "vit_h"
# input_point = np.array([[255,237]])  # Approx (x, y) where the tongue is visible
input_point = np.array([[x, y]])
input_label = np.array([1])  # 1 = positive label for tongue point

# === LOAD IMAGE ===
image = cv2.imread(image_path)
if image is None:
    print(f"❌ Image not found: {image_path}")
    exit()
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# === LOAD MODEL ===
device = "cuda" if torch.cuda.is_available() else "cpu"
print(device)
sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
sam.to(device)
predictor = SamPredictor(sam)
predictor.set_image(image_rgb)

# === PREDICT MASK ===
masks, _, _ = predictor.predict(
    point_coords=input_point,
    point_labels=input_label,
    multimask_output=False,
)
mask = masks[0]

# === APPLY MASK TO CREATE OUTPUT ===
output = np.zeros_like(image_rgb)
output[mask] = image_rgb[mask]

# === SAVE OUTPUT ===
cv2.imwrite(output_path, cv2.cvtColor(output, cv2.COLOR_RGB2BGR))
print(f"✅ Segmented tongue saved to: {output_path}")