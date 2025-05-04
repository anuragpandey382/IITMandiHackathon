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

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def process(img):
    img_np = np.array(img)
    # img_np = apply_clahe(img_np)
    img = Image.fromarray(img_np)

    transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
    ])

    input_tensor = transform(img).unsqueeze(0).to(device)
    return input_tensor

class Stage_1:
    def __init__(self):
        self.model = model = smp.DeepLabV3Plus(
            encoder_name="resnet34",
            encoder_weights="imagenet",
            in_channels=3,
            classes=1,
            activation=None
        ).to(device)
        
        self.model.load_state_dict(torch.load('checkpoint2_epoch_5.pth'))


    def forward(self, img):
        size_og = img.size

        self.model.eval()

        input_tensor = process(img)

        with torch.no_grad():
            output = self.model(input_tensor)
            prediction = (output.squeeze(0).squeeze(0) > 0.4).cpu().numpy().astype(np.uint8)
        
        prediction_resized = cv2.resize(prediction, size_og, interpolation=cv2.INTER_NEAREST)

        kernel = np.ones((3, 3), np.uint8)
        mask_closed = cv2.morphologyEx(prediction_resized, cv2.MORPH_CLOSE, kernel)

        original_img_np = np.array(img)

        masked_img = original_img_np * mask_closed[..., np.newaxis]

        return masked_img
