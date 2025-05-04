from torch.utils.data import Dataset
import cv2
import os
import torch
import numpy as np
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import random 
import matplotlib.pyplot as plt
import segmentation_models_pytorch as smp

IMG_SIZE = (1024,1024)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class Stage2:
    def __init__(self):
        self.unet_model = unet_model = smp.DeepLabV3Plus(
            encoder_name="resnet34",
            encoder_weights="imagenet",
            in_channels=1,
            classes=1,
            activation=None
        ).to(device)
        self.unet_model.load_state_dict(torch.load('checkpoint2_epoch_50.pth'))



    def preprocess_for_unet(self, masked_img):
        
        img = np.array(masked_img)
        img_green = img[:, :, 1]

        clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8, 8))
        img_green_clahe = clahe.apply(img_green)

        img_clahe_gray = Image.fromarray(img_green_clahe)

        transform = transforms.Compose([
            transforms.Resize(IMG_SIZE),
            transforms.ToTensor()
        ])

        img_tensor = transform(img_clahe_gray)


        return img_tensor
    
    def forward(self, masked_img,size_og):
        self.unet_model.eval()
        img = self.preprocess_for_unet(masked_img).to(device)

        with torch.no_grad():
            pred = self.unet_model(img.unsqueeze(0))[0][0].cpu().sigmoid().numpy()
            pred = (pred > 0.4).astype(np.uint8)

        pred = cv2.resize(pred, size_og, interpolation=cv2.INTER_NEAREST)
        return pred
