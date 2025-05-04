import cv2
import numpy as np
import streamlit as st
from PIL import Image
import matplotlib.pyplot as plt

def estimate_coating(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lower_white = np.array([0, 0, 180])
    upper_white = np.array([255, 60, 255])
    white_mask = cv2.inRange(hsv_image, lower_white, upper_white)
    coating_area = np.sum(white_mask) / (image.shape[0] * image.shape[1] * 255)
    return min(10, coating_area * 10), white_mask

def estimate_jagged_shape(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray_image, 100, 200)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return 0, edges
    jaggedness = sum([cv2.arcLength(cnt, False) for cnt in contours]) / len(contours)
    return min(10, jaggedness / 100), edges

def estimate_cracks(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    _, threshold_image = cv2.threshold(gray_image, 100, 255, cv2.THRESH_BINARY)
    edges = cv2.Canny(threshold_image, 50, 150)
    cracks = np.sum(edges) / (image.shape[0] * image.shape[1] * 255)
    return min(10, cracks * 10), edges

def estimate_papillae(image):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    lower_red = np.array([0, 30, 30])
    upper_red = np.array([10, 255, 255])
    red_mask = cv2.inRange(hsv_image, lower_red, upper_red)
    red_area = np.sum(red_mask) / (image.shape[0] * image.shape[1] * 255)
    papillae_size = min(10, red_area * 10)
    redness = papillae_size
    return papillae_size, redness, red_mask
def draw_center_rectangle(image, size=100, color=(0, 255, 0), thickness=2):
    h, w = image.shape[:2]
    center_y, center_x = h // 2, w // 2
    top_left = (center_x - size // 2, center_y - size // 2)
    bottom_right = (center_x + size // 2, center_y + size // 2)
    img_with_box = image.copy()
    cv2.rectangle(img_with_box, top_left, bottom_right, color, thickness)
    return img_with_box



def center_crop(image, size=1000):
    h, w = image.shape[:2]
    center_y, center_x = h // 2, w // 2
    half_size = size // 2
    cropped = image[center_y - half_size:center_y + half_size,
                    center_x - half_size:center_x + half_size]
    return cropped
# Streamlit UI
st.title("Tongue Feature Analyzer")


# Upload or Capture
option = st.radio("Choose image source", ["Upload Image", "Use Camera"])

img = None
if option == "Upload Image":
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        img = uploaded_file
else:
    img = st.camera_input("Capture Tongue Image")

def center_crop(image, size=100):
    h, w = image.shape[:2]
    cx, cy = w // 2, h // 2
    return image[cy - size//2:cy + size//2, cx - size//2:cx + size//2]

def draw_center_rectangle(image, size=100, color=(0, 255, 0), thickness=2):
    h, w = image.shape[:2]
    cx, cy = w // 2, h // 2
    pt1 = (cx - size//2, cy - size//2)
    pt2 = (cx + size//2, cy + size//2)
    return cv2.rectangle(image.copy(), pt1, pt2, color, thickness)

# === Estimation functions (reuse your existing ones) ===
# estimate_coating, estimate_jagged_shape, estimate_cracks, estimate_papillae

if img is not None:
    img_np = np.array(Image.open(img))
    image_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # Draw rectangle
    image_with_box = draw_center_rectangle(image_bgr, size=100)
    st.image(cv2.cvtColor(image_with_box, cv2.COLOR_BGR2RGB), caption="Image with 100x100 Box", use_column_width=True)

    # Crop & process
    cropped_image = center_crop(image_bgr, size=100)
    cropped_rgb = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)

    coating_score, coating_mask = estimate_coating(cropped_rgb)
    jagged_score, jagged_edges = estimate_jagged_shape(cropped_rgb)
    cracks_score, crack_edges = estimate_cracks(cropped_rgb)
    papillae_size, redness_score, red_mask = estimate_papillae(cropped_rgb)

    st.write(f"**Coating**: {coating_score:.2f}/10")
    st.write(f"**Jagged Shape**: {jagged_score:.2f}/10")
    st.write(f"**Cracks**: {cracks_score:.2f}/10")
    st.write(f"**Papillae Size / Redness**: {redness_score:.2f}/10")

    # Plot results
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    axes[0, 0].imshow(cropped_rgb); axes[0, 0].set_title("Cropped Image"); axes[0, 0].axis("off")
    axes[0, 1].imshow(coating_mask, cmap='gray'); axes[0, 1].set_title("Coating Mask"); axes[0, 1].axis("off")
    axes[0, 2].imshow(jagged_edges, cmap='gray'); axes[0, 2].set_title("Jagged Edges"); axes[0, 2].axis("off")
    axes[1, 0].imshow(crack_edges, cmap='gray'); axes[1, 0].set_title("Crack Edges"); axes[1, 0].axis("off")
    axes[1, 1].imshow(red_mask, cmap='gray'); axes[1, 1].set_title("Red Mask (Papillae)"); axes[1, 1].axis("off")
    axes[1, 2].axis("off")
    st.pyplot(fig)
