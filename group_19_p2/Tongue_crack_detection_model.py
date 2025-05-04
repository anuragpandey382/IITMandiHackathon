import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.filters import frangi
from skimage.morphology import skeletonize, erosion, disk
from skimage import img_as_ubyte
from skimage.exposure import rescale_intensity
from scipy.ndimage import distance_transform_edt


# --- Crack Metrics Calculation Functions ---
def calculate_length(contour):
    return cv2.arcLength(contour, True)

def calculate_width(contour):
    x, y, w, h = cv2.boundingRect(contour)
    return w

def calculate_score(num_cracks, total_length, avg_width, w1=1, w2=0.5, w3=0.7):
    return w1 * num_cracks + w2 * total_length + w3 * avg_width

def show_heatmap_overlay(original, frangi_scaled):
    heatmap = cv2.applyColorMap(frangi_scaled, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(cv2.resize(original, (256, 256)), 0.6, heatmap, 0.4, 0)
    return overlay


def detect_tongue_cracks_advanced(image_path):
    # Step 1: Load and resize image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error reading {image_path}")
        return
    image = cv2.resize(image, (256, 256))

    # Step 2: Tongue segmentation using GrabCut
    mask = np.zeros(image.shape[:2], np.uint8)
    rect = (10, 10, 236, 236)
    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)
    cv2.grabCut(image, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
    segmented = image * mask2[:, :, np.newaxis]
    segmented = np.full_like(image, 255)  # Ensure the background is white
    segmented[mask2 == 1] = image[mask2 == 1]

    # Step 3: Convert to grayscale
    gray = cv2.cvtColor(segmented, cv2.COLOR_BGR2GRAY)

    # Step 4: Erode the tongue mask to reduce edge effects
    mask_eroded = erosion(mask2, disk(10))
    gray_eroded = gray.copy()
    gray_eroded[mask_eroded == 0] = 255  # Set background to white

    # Step 5: CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray_eroded)

    # Step 6: Blur
    blurred = cv2.GaussianBlur(enhanced, (15, 15), 0)

    # Step 7: Frangi
    frangi_output = frangi(blurred)
    frangi_scaled = rescale_intensity(frangi_output, out_range=(0, 255)).astype(np.uint8)

    # Step 8: Threshold
    _, binary = cv2.threshold(frangi_scaled, 30, 255, cv2.THRESH_BINARY)

    # --- Boundary Removal with Distance Transform ---
    distance = distance_transform_edt(mask2)
    safe_mask = (distance > 15).astype(np.uint8)  # Exclude anything within 15 pixels of the boundary

    # Apply safe mask early (to binary image to preserve crack width)
    binary_no_boundary = cv2.bitwise_and(binary, binary, mask=safe_mask)

    # Step 9: Morphology
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morph = cv2.morphologyEx(binary_no_boundary, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Step 10: Skeletonize
    skeleton = skeletonize(morph > 0)
    skeleton_img = img_as_ubyte(skeleton)

    # Step 11: Final midline within safe mask
    final_midline = cv2.bitwise_and(skeleton_img, skeleton_img, mask=safe_mask.astype(np.uint8))

    # Step 12: Crack Analysis
    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    num_cracks = 0
    total_length = 0
    total_width = 0
    min_contour_area = 5

    contour_display = cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR)

    for contour in contours:
        if cv2.contourArea(contour) > min_contour_area:
            num_cracks += 1
            total_length += calculate_length(contour)
            total_width += calculate_width(contour)
            cv2.drawContours(contour_display, [contour], -1, (0, 255, 0), 1)

    avg_width = total_width / num_cracks if num_cracks > 0 else 0

    score = calculate_score(num_cracks, total_length, avg_width)
    score = score/100 
    score = min(10, max(0, score))  # Ensure score is between 0 and 10
    score = round(score, 2)

    # Output
    print(f"Number of Cracks: {num_cracks}")
    print(f"Total Length of Cracks: {total_length:.2f}")
    print(f"Average Width of Cracks: {avg_width:.2f}")
    print(f"Crack Severity Score: {score}")
    
    # Call visualization function
    overlay = show_heatmap_overlay(image, morph)

    return_dict = {
        "original": image,
        "segmented": segmented,
        "gray_eroded": gray_eroded,
        "morph": morph,
        "final_midline": final_midline,
        "contour_display": contour_display,
        "overlay": overlay,
        "num_cracks": num_cracks,
        "total_length": total_length,
        "avg_width": avg_width,
        "score": score,
        "contours": contours
    }
    # visualization(segmented, gray_eroded, morph, final_midline, contour_display,overlay)

    return return_dict

def visualization(segmented, gray_eroded, morph, final_midline, contour_display,overlay):
    # Display all images with white background
    plt.figure(figsize=(15, 8))

    plt.subplot(2, 3, 1)
    plt.title("Segmented Tongue")
    plt.imshow(cv2.cvtColor(segmented, cv2.COLOR_BGR2RGB))
    plt.axis("off")

    plt.subplot(2, 3, 2)
    plt.title("Eroded Input")
    plt.imshow(gray_eroded, cmap='gray')
    plt.axis("off")

    plt.subplot(2, 3, 3)
    plt.title("Morph After Boundary Removal")
    plt.imshow(morph, cmap='gray')
    plt.axis("off")

    plt.subplot(2, 3, 4)
    plt.title("Final Midline")
    plt.imshow(final_midline, cmap='gray')
    plt.axis("off")

    plt.subplot(2, 3, 5)
    plt.title("Detected Crack Contours")
    plt.imshow(cv2.cvtColor(contour_display, cv2.COLOR_BGR2RGB))
    plt.axis("off")

    plt.subplot(2, 3, 6)
    plt.title("Overlay with Heatmap")
    plt.imshow(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
    plt.imshow(cv2.cvtColor(contour_display, cv2.COLOR_BGR2RGB), alpha=0.5)
    plt.axis("off")

    plt.tight_layout()
    plt.show()


    # print(f"Results saved to {output_path}")
