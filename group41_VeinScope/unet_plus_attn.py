import torch
import numpy as np
import cv2
import os
from unet_attention import AttentionUNet

def load_model(checkpoint_path, model, optimizer=None,device='cpu'):
    checkpoint = torch.load(checkpoint_path,map_location=torch.device(device))
    model.load_state_dict(checkpoint['model_state_dict'])
    if optimizer:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    return model

def apply_clahe(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced_img = cv2.merge((l, a, b))
    return cv2.cvtColor(enhanced_img, cv2.COLOR_LAB2BGR)

class Vessels():
    def __init__(self, model_path, patch_size=256, stride=128, threshold=0.5,device='cpu'):
        self.device = device
        # self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = AttentionUNet(3, 1)
        print(model_path)
        self.model = load_model(model_path, self.model,device=self.device).to(self.device)
        self.model.eval()
        self.threshold = threshold
        self.patch_size = patch_size
        self.stride = stride
    
    def predict(self, img):
        original_img = img.copy()
        img = self.preprocess_img(img)
        output_img = self.predict_and_stitch(img)
        
        return output_img,original_img

        
    
    def preprocess_img(self, img):
        img = apply_clahe(img)
        img = img.transpose(2, 0, 1) / 255.0  # Convert to [C, H, W] and normalize
        return img
    
    def predict_and_stitch(self, image):
        C, H, W = image.shape  # Channels, Height, Width of the image
        stitched_img = np.zeros((C, H, W), dtype=np.float32)  # To store the stitched result
        weight_map = np.zeros((C, H, W), dtype=np.float32)  # To accumulate weights (for averaging overlapping areas)

        # Loop over the image in patches
        for y in range(0, H - self.patch_size + 1, self.stride):
            for x in range(0, W - self.patch_size + 1, self.stride):
                patch = image[:, y:y+self.patch_size, x:x+self.patch_size]
                patch = torch.tensor(patch, dtype=torch.float32).unsqueeze(0).to(self.device)  # Add batch dimension and move to device

                # Predict on the patch
                with torch.no_grad():
                    pred_patch = self.model(patch)
                    pred_patch = torch.sigmoid(pred_patch).cpu().numpy()  # Apply sigmoid and move back to CPU
                
                # Get the corresponding area in the full image to place the patch
                stitched_img[:, y:y+self.patch_size, x:x+self.patch_size] += pred_patch[0]  # Add the predicted patch
                weight_map[:, y:y+self.patch_size, x:x+self.patch_size] += 1  # Add weight to this area

        # Normalize the stitched image (average overlapping areas)
        epsilon = 1e-8  # Small constant to avoid division by zero
        weight_map = np.maximum(weight_map, epsilon)  # Prevent division by zero by setting zeros to epsilon
        stitched_img /= weight_map
        stitched_img = np.clip(stitched_img, 0, 1)  # Ensure values are between 0 and 1
        stitched_img = (stitched_img[0] > self.threshold).astype(np.uint8) * 255  # Only take the first channel

        return stitched_img
    
    def overlay_mask_on_image(self, image, mask, color=(255, 255, 0), alpha=0.5):
        """
        image: Original BGR image [H, W, 3]
        mask: Binary mask [H, W], values 0 or 255
        color: Tuple, color of mask overlay in BGR (default is red)
        alpha: Blending factor
        """
        # Ensure mask is binary and 3-channel
        mask_color = np.zeros_like(image)
        mask_bool = mask.astype(bool)
        mask_color[mask_bool] = color  # Apply color to mask area

        # Blend the original image and the color mask
        overlayed = cv2.addWeighted(image, 1.0, mask_color, alpha, 0)
        return overlayed

        


if __name__ == '__main__':
    # Load the trained model
    best_model_path = 'ckpts\\vein_ckpt.pt'    
    vessel_model = Vessels(best_model_path)

    # Load image to be predicted
    image_path = '1R_l_2.jpg'
    img = cv2.imread(image_path)  # Read image [H, W, C]
    
    stitched_img = vessel_model.predict(img, True)
    
    # print(stitched_img.shape, stitched_img.dtype)
    
    # # Save the stitched image
    # output_path = '/home/sidhant/Projects/DL_hackathon/inference/stitched_output.jpg'  # Define your output path
    # x = cv2.imwrite(output_path, stitched_img)
    # print(x)