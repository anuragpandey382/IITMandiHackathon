import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage.filters import frangi
from skimage.morphology import skeletonize
from skimage.measure import label, regionprops
from scipy.spatial.distance import euclidean

def calculate_vessel_redness(original_image, vessel_mask, sclera_mask):
    """Calculate redness using original image and binary masks"""
    # Extract only vessel pixels within sclera
    vessel_pixels = original_image[(vessel_mask > 0) & (sclera_mask > 0)]
    
    if len(vessel_pixels) == 0:
        return 0.0, 0.0
    
    # Split channels (OpenCV uses BGR)
    b, g, r = vessel_pixels[:, 0], vessel_pixels[:, 1], vessel_pixels[:, 2]
    
    # Method 1: Pure red intensity
    avg_red = np.mean(r)
    
    # Method 2: Normalized redness
    total = r + g + b
    total[total == 0] = 1  # Avoid division by zero
    redness_ratio = np.mean(r / total)
    
    return avg_red, redness_ratio

def calculate_vessel_length(vessel_mask):
    """Calculate total vessel length using skeletonization"""
    skeleton = skeletonize(vessel_mask // 255)
    return np.sum(skeleton)

def calculate_vessel_tortuosity(vessel_mask):
    """Calculate tortuosity (curviness) of vessels"""
    contours, _ = cv2.findContours(vessel_mask.astype(np.uint8), 
                                 cv2.RETR_EXTERNAL, 
                                 cv2.CHAIN_APPROX_NONE)
    
    tortuosity = []
    for contour in contours:
        if len(contour) < 10:  # Skip small contours
            continue
            
        # Calculate path length
        path_length = cv2.arcLength(contour, closed=False)
        
        # Calculate straight-line distance between endpoints
        endpoints = [contour[0][0], contour[-1][0]]
        straight_dist = euclidean(endpoints[0], endpoints[1]) + 1e-6
        
        tortuosity.append(path_length / straight_dist)
    
    return np.mean(tortuosity) if tortuosity else 1.0

def calculate_vessel_density(vessel_mask, sclera_mask):
    """Calculate percentage of sclera area covered by vessels"""
    vessel_area = np.sum((vessel_mask > 0) & (sclera_mask > 0))
    sclera_area = np.sum(sclera_mask > 0)
    return (vessel_area / sclera_area) if sclera_area > 0 else 0.0

def classify_health_indicator(redness, length, tortuosity, density):
    """Classify health condition based on metrics"""
    if redness > 160 and tortuosity > 1.5 and length > 100:
        return "Liver Stress / Alcohol Use"
    elif redness > 140 and tortuosity > 1.3:
        return "Fatigue"
    elif redness > 130 and density > 0.25:
        return "Allergy / Irritation"
    elif redness < 100 and density < 0.15:
        return "Dehydration"
    else:
        return "Normal / Healthy"

def analyze_eye_image(image_path):
    """Complete pipeline for eye image analysis"""
    # Load and preprocess image
    img_bgr = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    # Extract RGB channels
    red, green, blue = img_rgb[:, :, 0], img_rgb[:, :, 1], img_rgb[:, :, 2]
    
    # Compute redness map
    redness = red.astype(np.int16) - ((green + blue) / 2).astype(np.int16)
    redness_norm = cv2.normalize(redness, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    # Create sclera mask
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    _, sclera_mask = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    sclera_mask = cv2.morphologyEx(sclera_mask, cv2.MORPH_OPEN, np.ones((5,5), np.uint8))
    
    # Detect vessels using Frangi filter
    masked_redness = cv2.bitwise_and(redness_norm, redness_norm, mask=sclera_mask)
    vessels = frangi(masked_redness / 255.0)
    vessels_binary = (vessels > 0.2).astype(np.uint8) * 255
    
    # Calculate metrics
    avg_redness, redness_ratio = calculate_vessel_redness(img_bgr, vessels_binary, sclera_mask)
    total_length = calculate_vessel_length(vessels_binary)
    avg_tortuosity = calculate_vessel_tortuosity(vessels_binary)
    density = calculate_vessel_density(vessels_binary, sclera_mask)
    
    # Classify condition
    diagnosis = classify_health_indicator(avg_redness, total_length, avg_tortuosity, density)
    
    # Visualization
    skeleton = skeletonize(vessels_binary // 255).astype(np.uint8)
    
    plt.figure(figsize=(16, 6))
    plt.subplot(1, 4, 1)
    plt.imshow(img_rgb)
    plt.title("Original Image")
    plt.axis('off')
    
    plt.subplot(1, 4, 2)
    plt.imshow(masked_redness, cmap='Reds')
    plt.title("Sclera Redness")
    plt.axis('off')
    
    plt.subplot(1, 4, 3)
    plt.imshow(vessels_binary, cmap='gray')
    plt.title("Detected Vessels")
    plt.axis('off')
    
    plt.subplot(1, 4, 4)
    plt.imshow(skeleton, cmap='gray')
    plt.title("Skeletonized Vessels")
    plt.axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # Print results
    print("\n=== Analysis Results ===")
    print(f"Average Redness Level: {avg_redness:.2f}")
    print(f"Total Vessel Length: {total_length} pixels")
    print(f"Average Tortuosity: {avg_tortuosity:.2f}")
    print(f"Vessel Density: {density:.4f}")
    print(f"\nDiagnosis: {diagnosis}")

# Example usage
# image_path = r"C:/Users/aryan/Desktop/CS-671 Hackathon/SBVPI/2/2L_l_1.jpg"
# analyze_eye_image(image_path)

def preprocess_mask(mask):
    """Ensure mask is single-channel binary with values 0 or 255"""
    if mask.ndim == 3:
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    mask = mask.astype(np.float32)
    if np.max(mask) <= 1.0:  # If float mask in 0.0–1.0
        mask *= 255
    _, binary_mask = cv2.threshold(mask.astype(np.uint8), 127, 255, cv2.THRESH_BINARY)
    return binary_mask

def analyze_eye_image_from_arrays(img_bgr, sclera_mask, vessels_mask, show=False):
    """Pipeline for eye image analysis using precomputed masks (from a model)"""
    # Ensure correct formats
    if sclera_mask.ndim == 3:
        sclera_mask = cv2.cvtColor(sclera_mask, cv2.COLOR_BGR2GRAY)
    if vessels_mask.ndim == 3:
        vessels_mask = cv2.cvtColor(vessels_mask, cv2.COLOR_BGR2GRAY)

    # Threshold if not binary already
    _, sclera_mask = cv2.threshold(sclera_mask, 127, 255, cv2.THRESH_BINARY)
    _, vessels_binary = cv2.threshold(vessels_mask, 127, 255, cv2.THRESH_BINARY)

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Calculate metrics
    avg_redness, redness_ratio = calculate_vessel_redness(img_bgr, vessels_binary, sclera_mask)
    total_length = calculate_vessel_length(vessels_binary)
    avg_tortuosity = calculate_vessel_tortuosity(vessels_binary)
    density = calculate_vessel_density(vessels_binary, sclera_mask)
    
    # Classify condition
    diagnosis = classify_health_indicator(avg_redness, total_length, avg_tortuosity, density)
    
    # Visualization
    skeleton = skeletonize(vessels_binary // 255).astype(np.uint8)
    
    if show:
        plt.figure(figsize=(16, 6))
        plt.subplot(1, 3, 1)
        plt.imshow(img_rgb)
        plt.title("Original Image")
        plt.axis('off')
        
        plt.subplot(1, 3, 2)
        plt.imshow(vessels_binary, cmap='gray')
        plt.title("Detected Vessels")
        plt.axis('off')
        
        plt.subplot(1, 3, 3)
        plt.imshow(skeleton, cmap='gray')
        plt.title("Skeletonized Vessels")
        plt.axis('off')
        
        plt.tight_layout()
        plt.show()
    
        # Print results
        print("\n=== Analysis Results ===")
        print(f"Average Redness Level: {avg_redness:.2f}")
        print(f"Total Vessel Length: {total_length} pixels")
        print(f"Average Tortuosity: {avg_tortuosity:.2f}")
        print(f"Vessel Density: {density:.4f}")
        print(f"\nDiagnosis: {diagnosis}")

    results = {
        "Average Redness Level" : avg_redness,
        "Total Vessel Length" : total_length,
        "Average Tortuosity" : avg_tortuosity,
        "Vessel Density" : density,
        "Diagnosis" : diagnosis
    }

    return results

if __name__ == '__main__':
    img_bgr = cv2.imread('path/to/image.png') 
    model_output_sclera = cv2.imread('path/to/sclera.png', cv2.IMREAD_GRAYSCALE)
    model_output_vessels = cv2.imread('path/to/vessels.png', cv2.IMREAD_GRAYSCALE)
    results = analyze_eye_image_from_arrays(img_bgr, model_output_sclera, model_output_vessels)
    print(results)
