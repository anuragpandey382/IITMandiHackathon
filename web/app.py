"""
    TESTING IMPROVEMENT
"""
import os
import io
import base64
import torch
import cv2
import numpy as np
from pathlib import Path
from flask import Flask, request, jsonify, render_template
from fastai.vision.all import *

# Import necessary fastai components explicitly for clarity and robustness
from fastai.vision.all import MaskBlock
from PIL import Image
from fastai.data.transforms import Normalize
from flask_cors import CORS

# Import components for feature extraction and clustering
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
import joblib
from skimage import morphology
from scipy.ndimage import distance_transform_edt
from scipy.special import softmax


class AdvancedVesselPreprocessing(ItemTransform):
    """Advanced preprocessing specifically for eye vessel segmentation."""
    def __init__(self, clip_limit=4.0, tile_grid_size=(10, 10), use_gabor=False):
        store_attr()

    def encodes(self, img: PILImage):
        cv2.ocl.setUseOpenCL(False)

        if img.mode != 'RGB':
            img = img.convert('RGB')

        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        lab = cv2.cvtColor(cv_img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=(10, 10))
        l_clahe = clahe.apply(l)

        if self.use_gabor:
             kernel_size = 15
             sigma = 5
             theta = np.pi/4
             lambd = 10.0
             gamma = 0.5
             psi = 0
             gabor_kernel = cv2.getGaborKernel((kernel_size, kernel_size), sigma, theta, lambd, gamma, psi, ktype=cv2.CV_32F)
             l_enhanced = cv2.filter2D(l_clahe, cv2.CV_8UC1, gabor_kernel)
             l_enhanced = cv2.normalize(l_enhanced, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        else:
            l_enhanced = l_clahe

        lab_enhanced = cv2.merge((l_enhanced, a, b))
        img_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

        img_gray = cv2.cvtColor(img_enhanced, cv2.COLOR_BGR2GRAY)
        processed = cv2.merge([img_gray, img_gray, img_gray])

        return PILImage.create(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))

class EnhancedSegmentationLoss:
    """Combined loss for better vessel segmentation with boundary emphasis."""
    def __init__(self, dice_weight=0.7, bce_weight=0.15, focal_weight=0.15, gamma=2.0):
        self.dice_weight = dice_weight
        self.bce_weight = bce_weight
        self.focal_weight = focal_weight
        self.gamma = gamma
        self.bce = BCEWithLogitsLossFlat(axis=1)

    def __call__(self, pred, targ):
        if targ.ndim < pred.ndim:
            targ = targ.unsqueeze(1)

        pred_sigmoid = torch.sigmoid(pred)
        intersection = (pred_sigmoid * targ).sum()
        union = pred_sigmoid.sum() + targ.sum()
        dice_loss = 1 - (2. * intersection + 1e-6) / (union + 1e-6)

        bce_loss = self.bce(pred, targ)

        pt = targ * pred_sigmoid + (1 - targ) * (1 - pred_sigmoid)
        pt = pt.clamp(min=1e-6)
        focal_loss = torch.mean(-((1 - pt) ** self.gamma) * torch.log(pt))

        return (self.dice_weight * dice_loss +
                self.bce_weight * bce_loss +
                self.focal_weight * focal_loss)

def dice_vessel(inp, targ, smooth=1e-6):
    """Dice coefficient metric for vessel segmentation."""
    inp = (inp.sigmoid() > 0.5).float()
    targ = targ.float()
    intersection = (inp * targ).sum()
    return (2. * intersection + smooth) / (inp.sum() + targ.sum() + smooth)

def skeletonize_image(binary_image):
    """Skeletonize a binary image."""
    # Ensure the input is boolean for morphology.skeletonize
    return morphology.skeletonize(binary_image.astype(bool))

def find_branch_points(skel):
    """Find branch points in a skeletonized image."""
    skel_uint8 = skel.astype(np.uint8)
    branch_points = 0
    for i in range(1, skel_uint8.shape[0]-1):
        for j in range(1, skel_uint8.shape[1]-1):
            if skel_uint8[i, j] == 1:
                # Sum of 8 neighbors
                neighborhood_sum = np.sum(skel_uint8[i-1:i+2, j-1:j+2]) - skel_uint8[i, j]
                # A branch point typically has more than 2 connections (sum > 3 including itself)
                # After subtracting the center pixel, a sum > 2 indicates a branch point
                if neighborhood_sum > 2: # Corrected logic for sum of neighbors excluding center
                    branch_points += 1
    return branch_points

def find_endpoints(skel):
    """Find endpoints in a skeletonized image."""
    skel_uint8 = skel.astype(np.uint8)
    endpoints = 0
    for i in range(1, skel_uint8.shape[0]-1):
        for j in range(1, skel_uint8.shape[1]-1):
            if skel_uint8[i, j] == 1:
                # Sum of 8 neighbors
                neighborhood_sum = np.sum(skel_uint8[i-1:i+2, j-1:j+2]) - skel_uint8[i, j]
                # An endpoint has exactly one neighbor (sum == 1 after subtracting center)
                if neighborhood_sum == 1: # Corrected logic for sum of neighbors excluding center
                    endpoints += 1
    return endpoints

# Define initial weights and softmax weights for feature extraction
initial_weights = np.array([1.0, 1.0, 2.0, 1.5, 2.0, 2.5, 3.5])
softmax_weights = softmax(initial_weights)

def extract_raw_features_from_mask(binary_mask_np, resize_shape=(512, 512)):
    """
    Extract raw features from a binary mask numpy array.
    Assumes binary_mask_np is a numpy array with values 0 or 255.
    Returns a dictionary of features.
    """
    print("DEBUG: Entering extract_raw_features_from_mask")
    # Ensure binary mask is 0 or 255
    _, binary = cv2.threshold(binary_mask_np, 127, 255, cv2.THRESH_BINARY)

    # Resize the binary mask for feature extraction
    resized_binary = cv2.resize(binary, resize_shape, interpolation=cv2.INTER_NEAREST)

    # Ensure resized mask is strictly 0 or 255
    resized_binary = (resized_binary > 0).astype(np.uint8) * 255

    # Handle case with no vessels detected
    if not np.any(resized_binary == 255):
        print("DEBUG: No vessels found in resized binary mask for feature extraction.")
        # Return default features if no vessels are found
        return {
            'density': 0.0,
            'branch_points': 0,
            'endpoints': 0,
            'tortuosity': 1.0,
            'vein_length': 0.0,
            'vein_width': 0.0,
            'raw_vector': np.zeros(7).tolist() # Include the raw vector for clustering
        }

    skel = skeletonize_image(resized_binary)
    print(f"DEBUG: Skeletonization complete. Skeleton sum: {np.sum(skel)}")

    vein_length = np.sum(skel)

    dist = distance_transform_edt(resized_binary // 255) # Distance transform on boolean mask
    vein_width = np.mean(dist[resized_binary == 255]) if np.any(resized_binary == 255) else 0

    density = np.sum(resized_binary == 255) / resized_binary.size

    bp = find_branch_points(skel)
    ep = find_endpoints(skel)

    coords = np.column_stack(np.where(skel))
    straight_line_dist = np.linalg.norm(coords[0] - coords[-1]) if len(coords) >= 2 else 0
    tortuosity = vein_length / straight_line_dist if straight_line_dist > 0 else 1.0

    # Raw features vector for clustering (matches training script structure)
    raw_vector = np.array([density, density, bp, ep, tortuosity, vein_length, vein_width])

    features = {
        'density': float(density), # Convert to float for JSON
        'branch_points': int(bp), # Convert to int for JSON
        'endpoints': int(ep), # Convert to int for JSON
        'tortuosity': float(tortuosity), # Convert to float for JSON
        'vein_length': float(vein_length), # Convert to float for JSON
        'vein_width': float(vein_width), # Convert to float for JSON
        'raw_vector': raw_vector.tolist() # Convert numpy array to list for JSON
    }
    print(f"DEBUG: Extracted features: {features}")
    print("DEBUG: Exiting extract_raw_features_from_mask")
    return features

# Define health indicator mapping for clustering results
HEALTH_INDICATOR_MAP = {
    0: "Fatigue",
    1: "About to Die",  # This label seems concerning; ensure it's appropriate for your use case
    2: "Healthy"
}

# --- End of Custom Components and Helper Functions ---


# Configuration
# Use the same IMG_SIZE as training
IMG_SIZE = (512, 512)
# Feature extraction size can remain smaller as it's for features, not segmentation
FEATURE_IMG_SIZE = (512, 512)

# Paths for models and cascade file
MODEL_WEIGHTS_PATH = Path('../unet_feat/models/bestmodel.pth')
SCALER_PATH = Path('../unet_feat/models/scaler.joblib')
KMEANS_PATH = Path('../unet_feat/models/kmeans.joblib')
# Path to the Haar Cascade file for eye detection
EYE_CASCADE_PATH = Path('./haarcascade_eye.xml') # Make sure this file exists

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Global variables for loaded models and cascade
learn = None
scaler = None
kmeans = None
eye_cascade = None # Global variable for the eye cascade classifier

def load_model():
    """Loads the fastai model weights, scaler, KMeans model, and Haar Cascade."""
    global learn, scaler, kmeans, eye_cascade
    print("DEBUG: Starting model loading...")
    try:
        # Create dummy data for DataBlock initialization without needing actual training data
        dummy_dir = Path('./dummy_data')
        dummy_dir.mkdir(parents=True, exist_ok=True)
        dummy_img_path = dummy_dir / 'dummy_image.png'
        dummy_mask_path = dummy_dir / 'dummy_mask.png'

        if not dummy_img_path.exists():
            # Create a dummy image matching the expected IMG_SIZE
            Image.new('RGB', IMG_SIZE).save(dummy_img_path)
            print(f"DEBUG: Created dummy image at {dummy_img_path.resolve()}")
        if not dummy_mask_path.exists():
             # Create a dummy mask matching the expected IMG_SIZE
             Image.new('L', IMG_SIZE, color=0).save(dummy_mask_path)
             print(f"DEBUG: Created dummy mask at {dummy_mask_path.resolve()}")

        # Recreate the DataBlock structure used for training
        data_block = DataBlock(
            blocks=(ImageBlock, MaskBlock(codes=['background', 'vessel'])),
            get_items=lambda x: [dummy_img_path.resolve()],
            splitter=RandomSplitter(valid_pct=0.0), # No validation split needed for inference dataloader
            get_y=lambda x: dummy_mask_path.resolve(),
            item_tfms=[
                AdvancedVesselPreprocessing(clip_limit=4.0, tile_grid_size=(10, 10)),
                Resize(IMG_SIZE, method='squish') # Use the correct IMG_SIZE
            ],
            batch_tfms=[
                Normalize.from_stats(*imagenet_stats),
            ]
        )
        # Create a dataloader using the dummy data
        dls = data_block.dataloaders(dummy_dir, bs=1, shuffle=False, drop_last=False)
        print("DEBUG: DataLoaders created with dummy data.")

        # Recreate the Learner structure
        learn = unet_learner(
            dls,
            resnet34, # Ensure this matches the architecture used in training
            n_out=1,
            metrics=[dice_vessel],
            loss_func=EnhancedSegmentationLoss(),
            wd=1e-2,
            path=Path('.'),
            model_dir=Path('./models').relative_to(Path('.')),
            self_attention=True # Ensure this matches the training setup
        )
        print("DEBUG: Learner architecture defined.")

        # Load the model weights
        if not MODEL_WEIGHTS_PATH.exists():
             print(f"ERROR: Segmentation model weights file not found at {MODEL_WEIGHTS_PATH.resolve()}")
             # Attempt to load the .pkl file as a fallback if .pth is not found
             model_paths_pkl = [FINAL_MODEL_STATE_PATH, MODEL_DIR / 'vessel_segmentation_model.pkl']
             loaded_pkl = False
             for mp in model_paths_pkl:
                 if mp.exists():
                     print(f"DEBUG: Attempting to load complete learner state from {mp}...")
                     try:
                         learn = load_learner(mp, cpu=True, pickle_module=pickle) # Force CPU load
                         learn.model.eval() # Ensure model is in evaluation mode
                         print(f"DEBUG: Model state (.pkl) loaded successfully from {mp}.")
                         loaded_pkl = True
                         break
                     except Exception as e:
                         print(f"ERROR: Error loading learner state from {mp}: {e}")
                         print("Please ensure the fastai version and pickle module are compatible.")
             if not loaded_pkl:
                  raise FileNotFoundError(f"Segmentation model weights file not found at {MODEL_WEIGHTS_PATH.resolve()} and no fallback .pkl found.")

        else:
            print(f"DEBUG: Attempting to load model weights from {MODEL_WEIGHTS_PATH.resolve()}...")
            try:
                learn.model.load_state_dict(torch.load(MODEL_WEIGHTS_PATH, map_location=torch.device('cpu')))
                learn.model.eval()  # Set the model to evaluation mode
                print("DEBUG: Model weights (.pth) loaded successfully.")
            except Exception as e:
                 print(f"ERROR: Error loading model weights from .pth: {e}")
                 print("Falling back to attempting to load the .pkl file.")
                 model_paths_pkl = [FINAL_MODEL_STATE_PATH, MODEL_DIR / 'vessel_segmentation_model.pkl']
                 loaded_pkl = False
                 for mp in model_paths_pkl:
                     if mp.exists():
                         print(f"DEBUG: Attempting to load complete learner state from {mp}...")
                         try:
                             learn = load_learner(mp, cpu=True, pickle_module=pickle) # Force CPU load
                             learn.model.eval() # Ensure model is in evaluation mode
                             print(f"DEBUG: Model state (.pkl) loaded successfully from {mp}.")
                             loaded_pkl = True
                             break
                         except Exception as e:
                             print(f"ERROR: Error loading learner state from {mp}: {e}")
                             print("Please ensure the fastai version and pickle module are compatible.")
                 if not loaded_pkl:
                     raise Exception("Failed to load model weights and no fallback .pkl could be loaded.")


        print("DEBUG: Loading Scaler and KMeans models...")
        if not SCALER_PATH.exists():
             print(f"WARNING: Scaler model not found at {SCALER_PATH.resolve()}. Feature normalization will not be performed.")
             scaler = None
        else:
             try:
                 scaler = joblib.load(SCALER_PATH)
                 print(f"DEBUG: Scaler model loaded successfully from {SCALER_PATH.resolve()}")
             except Exception as e:
                 print(f"ERROR: Error loading scaler model from {SCALER_PATH.resolve()}: {e}")
                 print("Please ensure scikit-learn versions match between training and inference environments.")
                 scaler = None


        if not KMEANS_PATH.exists():
             print(f"WARNING: KMeans model not found at {KMEANS_PATH.resolve()}. Clustering prediction will not be performed.")
             kmeans = None
        else:
             try:
                 kmeans = joblib.load(KMEANS_PATH)
                 print(f"DEBUG: KMeans model loaded successfully from {KMEANS_PATH.resolve()}")
             except Exception as e:
                 print(f"ERROR: Error loading KMeans model from {KMEANS_PATH.resolve()}: {e}")
                 print("Please ensure scikit-learn versions match between training and inference environments.")
                 kmeans = None

        # Load the Haar Cascade classifier for eye detection
        if not EYE_CASCADE_PATH.exists():
            print(f"WARNING: Eye cascade file not found at {EYE_CASCADE_PATH.resolve()}. ROI detection will be skipped.")
            eye_cascade = None
        else:
            eye_cascade = cv2.CascadeClassifier(str(EYE_CASCADE_PATH))
            if eye_cascade.empty():
                print(f"WARNING: Failed to load eye cascade from {EYE_CASCADE_PATH.resolve()}. ROI detection will be skipped.")
                eye_cascade = None
            else:
                print(f"DEBUG: Eye cascade classifier loaded successfully from {EYE_CASCADE_PATH.resolve()}")

        print("DEBUG: Model loading complete.")

    except FileNotFoundError as e:
        print(f"ERROR: File not found during model loading: {e}")
        print("Please ensure all required files exist at the specified paths.")
        learn = None
        scaler = None
        kmeans = None
        eye_cascade = None
    except Exception as e:
        print(f"ERROR: Generic error during model loading or setup: {e}")
        print("Check if the DataBlock, Learner arguments, custom components, and model files are correct.")
        learn = None
        scaler = None
        kmeans = None
        eye_cascade = None

# Load models and cascade when the Flask app starts
with app.app_context():
    load_model()

@app.route('/')
def index():
    # Assuming you have an index.html template
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    print("DEBUG: Received prediction request.")
    if learn is None:
        print("ERROR: Segmentation model not loaded.")
        return jsonify({'error': 'Segmentation model not loaded. Check server logs.'}), 500

    if 'image' not in request.files:
        print("ERROR: No image file provided in request.")
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        print("ERROR: No selected file name.")
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Read the image file from the request
        img_bytes = file.read()
        print(f"DEBUG: Read {len(img_bytes)} bytes from image file.")
        # Create a PIL Image from the bytes
        img_pil_orig = PILImage.create(io.BytesIO(img_bytes))
        print(f"DEBUG: Created PIL Image. Size: {img_pil_orig.size}, Mode: {img_pil_orig.mode}")
        # Convert PIL Image to OpenCV format (BGR) for cascade detection if needed
        img_cv_orig = cv2.cvtColor(np.array(img_pil_orig), cv2.COLOR_RGB2BGR)
        print(f"DEBUG: Converted to OpenCV image. Shape: {img_cv_orig.shape}")

        # Initialize variables for results
        final_binary_mask_np = np.zeros((img_cv_orig.shape[0], img_cv_orig.shape[1]), dtype=np.uint8)
        predicted_cluster = None
        health_indicator_text = "Clustering models not loaded."
        roi_area = 0 # Initialize ROI area
        feature_results = {} # Dictionary to store extracted features

        # --- ROI Detection ---
        roi_detected = False
        img_for_segmentation_pil = img_pil_orig # Default to full image
        print("DEBUG: Attempting ROI detection...")
        if eye_cascade is not None:
            gray = cv2.cvtColor(img_cv_orig, cv2.COLOR_BGR2GRAY)

            # Detect eyes in the grayscale image
            eyes = eye_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1, # Adjust as needed
                minNeighbors=5,  # Adjust as needed
                minSize=(50, 50) # Increased min size to reduce false positives
            )
            print(f"DEBUG: Detected {len(eyes)} potential eye regions.")

            if len(eyes) > 0:
                roi_detected = True
                # Simple logic to select the largest detected eye as the ROI
                eyes = sorted(eyes, key=lambda x: x[2] * x[3], reverse=True)
                (x, y, w, h) = eyes[0] # Select the largest eye

                # Add a small buffer around the detected eye region
                buffer_pixels = 50 # Adjust buffer size as needed
                x_start = max(0, x - buffer_pixels)
                y_start = max(0, y - buffer_pixels)
                x_end = min(img_cv_orig.shape[1], x + w + buffer_pixels)
                y_end = min(img_cv_orig.shape[0], y + h + buffer_pixels)

                # Calculate ROI area
                roi_area = (x_end - x_start) * (y_end - y_start)

                # Crop the ROI from the original PIL image
                img_for_segmentation_pil = img_pil_orig.crop((x_start, y_start, x_end, y_end))
                print(f"DEBUG: Eye ROI detected. Cropping image to ({x_start}, {y_start}, {x_end}, {y_end}) for segmentation. ROI Area: {roi_area}")

            else:
                print("DEBUG: No eyes detected using cascade. Segmenting the full image.")
                # If no eye detected, segment the full original image
                img_for_segmentation_pil = img_pil_orig
                health_indicator_text = "No eye ROI detected. Segmented full image."

        else:
            print("DEBUG: Eye cascade classifier not loaded. Segmenting the full image.")
            # If cascade is not loaded, segment the full original image
            img_for_segmentation_pil = img_pil_orig
            health_indicator_text = "Eye detection not available. Segmented full image."
        # --- End ROI Detection ---

        print(f"DEBUG: Image prepared for segmentation. Size: {img_for_segmentation_pil.size}")
        # Perform prediction on the selected image (either ROI or full image)
        # learn.predict handles the necessary preprocessing defined in the DataBlock, including resizing
        print("DEBUG: Calling learn.predict...")
        _, _, raw_logits_tensor = learn.predict(img_for_segmentation_pil)
        print("DEBUG: learn.predict completed.")

        # Apply sigmoid to get probabilities and remove batch dimension
        prob_tensor = torch.sigmoid(raw_logits_tensor).squeeze().cpu()
        print(f"DEBUG: Sigmoid applied. Probability tensor shape: {prob_tensor.shape}")

        # Convert probability tensor to numpy array
        prob_np = prob_tensor.numpy()
        print(f"DEBUG: Converted probability tensor to numpy array. Shape: {prob_np.shape}")

        # Apply threshold to get initial binary mask (values 0 or 1)
        binary_mask_np = (prob_np > 0.2).astype(np.uint8)
        print(f"DEBUG: Threshold applied (>0.2). Binary mask shape: {binary_mask_np.shape}, unique values: {np.unique(binary_mask_np)}")

        # --- Start of Post-processing Steps (Applied to the segmented mask) ---
        print("DEBUG: Starting post-processing (Connected Components + Closing)...")
        # 1. Connected Components Analysis to remove small artifacts
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_mask_np, connectivity=8)
        print(f"DEBUG: Connected components found: {num_labels}")

        min_size = 5 # Minimum size threshold for connected components (adjust if needed)
        clean_mask = np.zeros_like(binary_mask_np)
        # Iterate through components, skipping the background (label 0)
        if num_labels > 1:
            for j in range(1, num_labels):
                if stats[j, cv2.CC_STAT_AREA] >= min_size:
                    clean_mask[labels == j] = 1 # Keep components larger than min_size
        print(f"DEBUG: Cleaned mask using min_size={min_size}. Unique values: {np.unique(clean_mask)}")

        # Ensure clean_mask is 0 or 1 before morphology
        clean_mask = clean_mask.astype(np.uint8)

        # 2. Morphological Closing to fill small gaps and connect nearby segments
        kernel = np.ones((3, 3), np.uint8) # 3x3 kernel (adjust size if needed)
        # Apply closing: dilation followed by erosion
        processed_mask_np = cv2.morphologyEx(clean_mask, cv2.MORPH_CLOSE, kernel)
        print(f"DEBUG: Morphological closing applied. Unique values: {np.unique(processed_mask_np)}")

        # Convert the processed mask to 0 or 255
        processed_mask_255 = processed_mask_np * 255
        print(f"DEBUG: Processed mask scaled to 0/255. Unique values: {np.unique(processed_mask_255)}")
        print("DEBUG: Post-processing complete.")
        # --- End of Post-processing Steps ---


        # --- Place segmented mask onto original image canvas ---
        print("DEBUG: Placing segmented mask onto original image canvas...")
        if roi_detected:
            # If ROI was detected, resize the processed ROI mask back to the original ROI dimensions
            # The processed_mask_255 here is the mask for the CROPPED ROI, resized to IMG_SIZE by fastai
            # We need to resize it back to the original ROI dimensions (x_end-x_start, y_end-y_start)
            processed_roi_mask_resized = cv2.resize(processed_mask_255, (x_end - x_start, y_end - y_start), interpolation=cv2.INTER_NEAREST)
            print(f"DEBUG: Resized processed ROI mask to original ROI dimensions: {processed_roi_mask_resized.shape}")
            # Place the resized ROI mask onto the blank final mask canvas
            final_binary_mask_np[y_start:y_end, x_start:x_end] = processed_roi_mask_resized
            print("DEBUG: Segmented ROI placed onto original image canvas.")
            mask_for_features = processed_roi_mask_resized # Use the processed ROI mask for features
            print(f"DEBUG: Mask for features is processed ROI mask. Shape: {mask_for_features.shape}")
        else:
            # If no ROI detected, the segmented mask is for the full image (resized to IMG_SIZE by fastai)
            # The processed_mask_255 here is the mask for the FULL IMAGE, resized to IMG_SIZE
            # We need to resize it back to the original image size before returning and for features
            final_binary_mask_np = cv2.resize(processed_mask_255, (img_cv_orig.shape[1], img_cv_orig.shape[0]), interpolation=cv2.INTER_NEAREST)
            print(f"DEBUG: Segmented full image resized to original dimensions: {final_binary_mask_np.shape}")
            mask_for_features = final_binary_mask_np # Use the processed full mask for features
            print(f"DEBUG: Mask for features is processed full mask. Shape: {mask_for_features.shape}")
        # --- End Placing Mask ---


        # Ensure the final mask is 2D (should already be, but a safety check)
        if final_binary_mask_np.ndim == 3 and final_binary_mask_np.shape[2] == 1:
            final_binary_mask_np = final_binary_mask_np.squeeze(axis=2)
            print("DEBUG: Squeezed final_binary_mask_np dimension 2.")
        elif final_binary_mask_np.ndim == 3 and final_binary_mask_np.shape[0] == 1:
             final_binary_mask_np = final_binary_mask_np.squeeze(axis=0)
             print("DEBUG: Squeezed final_binary_mask_np dimension 0.")
        print(f"DEBUG: Final binary mask shape before encoding: {final_binary_mask_np.shape}")


        # --- Feature Extraction and Clustering ---
        print("DEBUG: Starting feature extraction and clustering...")
        # Perform feature extraction and clustering based on the processed mask
        if scaler is not None and kmeans is not None:
             try:
                  print("DEBUG: Scaler and KMeans models are loaded. Proceeding with feature extraction.")
                  # Extract features from the mask (resized to FEATURE_IMG_SIZE for feature extraction)
                  # Pass the 0/255 mask for feature extraction
                  feature_results = extract_raw_features_from_mask(mask_for_features, resize_shape=FEATURE_IMG_SIZE)
                  print(f"DEBUG: Raw features extracted: {feature_results}")

                  # Reshape features for the scaler
                  raw_features_vector = np.array(feature_results['raw_vector']).reshape(1, -1)
                  print(f"DEBUG: Raw features vector shape for scaler: {raw_features_vector.shape}")

                  # Normalize features using the loaded scaler
                  normalized_features = scaler.transform(raw_features_vector)
                  print(f"DEBUG: Normalized features: {normalized_features}")

                  # Apply softmax weights (if applicable, ensure this matches training)
                  weighted_features = normalized_features * softmax_weights
                  print(f"DEBUG: Weighted features: {weighted_features}")

                  # Predict the cluster using the loaded KMeans model
                  predicted_cluster = kmeans.predict(weighted_features)[0]
                  print(f"DEBUG: Predicted cluster ID: {predicted_cluster}")

                  # Map the cluster ID to a health indicator text
                  health_indicator_text = HEALTH_INDICATOR_MAP.get(predicted_cluster, f"Unknown Cluster ID: {predicted_cluster}")

                  print(f"DEBUG: Final Health Indicator Text: {health_indicator_text}")

             except Exception as e:
                 print(f"ERROR: Error during feature extraction or clustering: {e}")
                 health_indicator_text = f"Clustering failed: {e}"
                 predicted_cluster = None # Ensure cluster is None on failure
                 # Initialize feature_results with default values on failure
                 feature_results = {
                     'density': 0.0,
                     'branch_points': 0,
                     'endpoints': 0,
                     'tortuosity': 1.0,
                     'vein_length': 0.0,
                     'vein_width': 0.0,
                     'raw_vector': []
                 }
        else:
             print("DEBUG: Scaler or KMeans models are NOT loaded. Skipping feature extraction and clustering.")
             health_indicator_text = "Clustering models not loaded."
             predicted_cluster = None # Ensure cluster is None if models not loaded
             # Initialize feature_results with default values if models are not loaded
             feature_results = {
                 'density': 0.0,
                 'branch_points': 0,
                 'endpoints': 0,
                 'tortuosity': 1.0,
                 'vein_length': 0.0,
                 'vein_width': 0.0,
                 'raw_vector': []
             }
        print("DEBUG: Feature extraction and clustering complete.")
        # --- End of Feature Extraction and Clustering ---


        # Encode the final binary mask (0 or 255) as a PNG image in memory
        print("DEBUG: Encoding final binary mask...")
        is_success, buffer = cv2.imencode(".png", final_binary_mask_np)
        if not is_success:
            print("ERROR: Could not encode mask image.")
            return jsonify({'error': 'Could not encode mask image'}), 500
        print(f"DEBUG: Mask encoded successfully. Buffer size: {len(buffer)}")

        # Convert the image buffer to a Base64 string
        mask_base64 = base64.b64encode(buffer).decode('utf-8')
        print(f"DEBUG: Mask converted to Base64 string. Length: {len(mask_base64)}")

        # Return the Base64 image, clustering results, and detailed features as JSON
        response_data = {
            'mask_image_base64': mask_base64,
            'predicted_cluster': int(predicted_cluster) if predicted_cluster is not None else None,
            'health_indicator_text': health_indicator_text,
            'features': feature_results # Include the detailed feature results
        }
        print(f"DEBUG: Final JSON response data: {response_data}")

        return jsonify(response_data)

    except Exception as e:
        print(f"ERROR: Uncaught exception during prediction: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Prediction failed: {e}'}), 500

if __name__ == '__main__':
    print("=" * 80)
    print("Starting Flask server...")
    print("=" * 80)
    # Run the Flask app
    # debug=True should be False in production
    # host='0.0.0.0' makes the server accessible externally
    app.run(debug=True, host='0.0.0.0', port=5001)
