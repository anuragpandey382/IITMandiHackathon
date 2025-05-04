# custom_components.py
# This file contains the definitions of all custom classes and functions
# used in your fastai learner training script.
# It needs to be in the same directory as app.py so it can be imported.

import torch
import cv2
from pathlib import Path
import numpy as np
from PIL import Image as PILImage_module # Used in fix_masks and batch prediction saving
# Import necessary fastai libraries and specific components
from fastai.vision.all import *
from fastai.losses import BCEWithLogitsLossFlat # Ensure this is imported if used in EnhancedSegmentationLoss
# Add any other specific fastai imports your custom code might need
# Ensure custom components are correctly imported


# --- Configuration (Include relevant parts if used by functions here) ---
# These are needed by get_all_image_files and get_mask_path
MASK_SUFFIX = "_vessels.png"


# --- Enhanced Preprocessing Functions (Used in DataBlock) ---
# This class definition must exactly match the one used in your training script.
class AdvancedVesselPreprocessing(ItemTransform):
    """Advanced preprocessing specifically for eye vessel segmentation."""
    def __init__(self, clip_limit=4.0, tile_grid_size=(10, 10), use_gabor=False): # Added use_gabor flag
        store_attr()
        # Optional: Pre-calculate Gabor kernels if using Gabor filtering
        # self.gabor_kernels = []
        # if self.use_gabor:
        #     kernel_size = 15
        #     sigma = 5
        #     lambd = 10.0
        #     gamma = 0.5
        #     # Create kernels for multiple orientations
        #     for theta in np.arange(0, np.pi, np.pi / 4): # Example: 4 orientations
        #         kernel = cv2.getGaborKernel((kernel_size, kernel_size), sigma, theta, lambd, gamma, 0, ktype=cv2.CV_32F)
        #         self.gabor_kernels.append(kernel)


    def encodes(self, img: PILImage):
        # Ensure OpenCL is disabled to prevent issues
        cv2.ocl.setUseOpenCL(False)

        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Convert to OpenCV format
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        # Convert to Lab color space - CLAHE often works better on L channel
        lab = cv2.cvtColor(cv_img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=self.tile_grid_size)
        l_clahe = clahe.apply(l)

        # Optional: Apply unsharp mask to enhance edges (vessels)
        # l_clahe = cv2.addWeighted(l_clahe, 1.5, cv2.GaussianBlur(l_clahe, (0,0), 5), -0.5, 0) # Example unsharp mask

        # Apply Gabor filtering if enabled
        if self.use_gabor:
             # This is a simplified example; a real implementation would apply
             # multiple kernels and combine the results (e.g., take the maximum response)
             # For demonstration, applying a single Gabor kernel
             kernel_size = 15
             sigma = 5
             theta = np.pi/4 # Example orientation
             lambd = 10.0
             gamma = 0.5
             psi = 0
             gabor_kernel = cv2.getGaborKernel((kernel_size, kernel_size), sigma, theta, lambd, gamma, psi, ktype=cv2.CV_32F)
             l_enhanced = cv2.filter2D(l_clahe, cv2.CV_8UC1, gabor_kernel) # Use CV_8UC1 for single channel output
             # Normalize Gabor output to 0-255
             l_enhanced = cv2.normalize(l_enhanced, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

        else:
            # Use CLAHE enhanced channel if Gabor is not used
            l_enhanced = l_clahe


        # Merge the enhanced L channel (or Gabor output) back with original a and b channels
        # Note: If using Gabor, l_enhanced is now a single channel image
        # We'll merge it back as the L channel
        lab_enhanced = cv2.merge((l_enhanced, a, b))

        # Convert back to BGR
        img_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

        # Convert to grayscale (by taking the enhanced L channel) and then 3-channel
        img_gray = cv2.cvtColor(img_enhanced, cv2.COLOR_BGR2GRAY)
        processed = cv2.merge([img_gray, img_gray, img_gray])


        # Convert back to PIL
        return PILImage.create(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))


# --- Enhanced Loss Function ---
# This class definition must exactly match the one used in your training script.
class EnhancedSegmentationLoss:
    """Combined loss for better vessel segmentation with boundary emphasis."""
    # Consider adjusting weights if vessels are extremely sparse
    def __init__(self, dice_weight=0.7, bce_weight=0.15, focal_weight=0.15, gamma=2.0): # Increased Dice weight again
        store_attr()
        self.bce = BCEWithLogitsLossFlat(axis=1)

    def __call__(self, pred, targ):
        # Ensure target has same dimension as prediction
        if targ.ndim < pred.ndim:
            targ = targ.unsqueeze(1)

        # Dice loss component
        pred_sigmoid = torch.sigmoid(pred)
        intersection = (pred_sigmoid * targ).sum()
        union = pred_sigmoid.sum() + targ.sum()
        dice_loss = 1 - (2. * intersection + 1e-6) / (union + 1e-6)

        # BCE loss component
        bce_loss = self.bce(pred, targ)

        # Focal loss component - emphasizes hard-to-classify examples
        pt = targ * pred_sigmoid + (1 - targ) * (1 - pred_sigmoid)
        pt = pt.clamp(min=1e-6) # Clamp to prevent log(0)
        focal_loss = torch.mean(-((1 - pt) ** self.gamma) * torch.log(pt))


        # Combine losses
        return (self.dice_weight * dice_loss +
                self.bce_weight * bce_loss +
                self.focal_weight * focal_loss)

# --- Custom Dice Score Metric ---
# This function definition must exactly match the one used in your training script.
def dice_vessel(inp, targ, smooth=1e-6):
    """Dice coefficient metric for vessel segmentation."""
    inp = (inp.sigmoid() > 0.5).float()  # Convert logits to binary prediction
    targ = targ.float()
    intersection = (inp * targ).sum()
    return (2. * intersection + smooth) / (inp.sum() + targ.sum() + smooth)

# --- Helper Functions for DataBlock ---
# These function definitions must exactly match the ones used in your training script.
def get_all_image_files(path):
    """Find all valid image files that have corresponding vessel mask files."""
    files = []

    # print(f"Scanning for image-mask pairs in {path}...") # Keep print for debugging if needed
    all_images = get_image_files(path, recurse=True, folders=None)

    # Filter by extension if needed
    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    all_images = [f for f in all_images if f.suffix.lower() in valid_exts]

    for img_file in all_images:
        # Skip any mask files or other specific masks from the input list
        if MASK_SUFFIX not in img_file.name and \
           "_sclera" not in img_file.name and \
           "_periocular" not in img_file.name and \
           "_canthus" not in img_file.name and \
           "_iris" not in img_file.name and \
           "_pupil" not in img_file.name and \
           "_eyelashes" not in img_file.name and \
           "_pred" not in img_file.name: # Also skip previously saved predictions

            # Check if corresponding vessel mask exists
            mask_file = img_file.parent / f"{img_file.stem}{MASK_SUFFIX}"
            if mask_file.exists():
                files.append(img_file)

    # print(f"Found {len(files)} images with corresponding '{MASK_SUFFIX}' masks.") # Keep print for debugging if needed

    if not files:
        # print("WARNING: No valid image-mask pairs found for training!") # Keep print for debugging if needed
        pass # Don't need a warning here if just loading for prediction
    return files

def get_mask_path(img_path):
    """Get the corresponding mask path for an image file."""
    return img_path.parent / f"{img_path.stem}{MASK_SUFFIX}"

# Add definitions for any other custom functions or classes if you used them
# in your training script and they are not standard fastai components.
# For example, if you had a custom callback, its definition would go here.

