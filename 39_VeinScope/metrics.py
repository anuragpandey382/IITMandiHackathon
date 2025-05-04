import numpy as np
from skimage.metrics import structural_similarity as ssim

def mse(image1, image2):
    assert image1.shape == image2.shape, "Images must have the same dimensions" 
    return np.mean((image1 - image2) ** 2)

def ssim_score(image1, image2):
    image1 = image1.astype(float)
    image2 = image2.astype(float)
    data_range = image1.max() - image1.min()
    
    return ssim(image1, image2, multichannel=True, data_range=data_range)

def ncc(image1, image2):
    assert image1.shape == image2.shape, "Images must have the same dimensions"
    
    image1 = image1 - np.mean(image1)
    image2 = image2 - np.mean(image2)
    numerator = np.sum(image1 * image2)
    denominator = np.sqrt(np.sum(image1 ** 2) * np.sum(image2 ** 2))
    
    return numerator / denominator

def psnr(image1, image2):
    mse_val = mse(image1, image2)
    if mse_val == 0:
        return float('inf')
    max_pixel = 255.0
    return 20 * np.log10(max_pixel / np.sqrt(mse_val))

def dice_score(pred, gt):
    assert pred.shape == gt.shape, "Prediction and Ground Truth must have the same shape"
    
    pred = pred.astype(bool)
    gt = gt.astype(bool)

    intersection = np.logical_and(pred, gt).sum()
    total = pred.sum() + gt.sum()
    
    if total == 0:
        return 1.0 
    return 2.0 * intersection / total
