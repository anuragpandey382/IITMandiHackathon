import stage1
import stage2
from PIL import Image
import matplotlib.pyplot as plt
import cv2
import numpy as np
import os
from disease_mapping import *


DISEASE_ROOT = 'stages/images_for_disease/'

def process(img_path):
    img_og = Image.open(img_path).convert('RGB')
    size_og = img_og.size

    model1 = stage1.Stage_1()
    masked_img = model1.forward(img_og)
    model2 = stage2.Stage2()
    pred = model2.forward(masked_img,size_og)

    dis = map_disease(img_path)
    print("Image Analysis for disease (Preliminary - Not properly cited)\n\n")

    for i in dis:
        print(f"{i}\t\t\t{dis[i]}")


    return pred, img_og


def process_disease(img_path):
    img_og = Image.open(img_path).convert('RGB')
    size_og = img_og.size

    model1 = stage1.Stage_1()
    masked_img = model1.forward(img_og)
    model2 = stage2.Stage2()
    pred = model2.forward(masked_img,size_og)

    disease = map_disease(img_path)
    return pred, img_og, disease



def visualize(img_path):
    pred, img_og = process(img_path)

    plt.figure(figsize=(10, 5))

    # Original image
    plt.subplot(1, 2, 1)
    plt.title("Original Image")
    plt.imshow(img_og)
    plt.axis('off')

    # Overlay
    plt.subplot(1, 2, 2)
    plt.title("Overlay of Predicted")
    plt.imshow(img_og)
    plt.imshow(pred, cmap='Greens', alpha=0.3)  # Overlay with transparency
    plt.axis('off')

    plt.tight_layout()
    plt.show()


def process_all(img_path):
    img_og = Image.open(img_path).convert('RGB')
    size_og = img_og.size

    model1 = stage1.Stage_1()
    masked_img = model1.forward(img_og)
    model2 = stage2.Stage2()
    pred = model2.forward(masked_img,size_og)
    return img_og, masked_img, pred

def stage_visualize(img_path):
    img_og, masked_img, pred = process_all(img_path)
    # Display the images
    plt.figure(figsize=(20, 5))
    plt.subplot(1, 4, 1)
    plt.title("Original Image")
    plt.imshow(img_og)
    plt.axis('off')

    plt.subplot(1, 4, 2)
    plt.title("Masked Image (Stage 1 Output)")
    plt.imshow(masked_img)
    plt.axis('off')

    plt.subplot(1, 4, 3)
    plt.title("Prediction (Stage 2 Output)")
    plt.imshow(pred, cmap = 'grey')
    plt.axis('off')

    plt.subplot(1, 4, 4)
    plt.title("Overlay of Predicted")
    plt.imshow(img_og)
    plt.imshow(pred, cmap='Greens', alpha=0.3)  # Overlay with transparency
    plt.axis('off')

    plt.tight_layout()
    plt.show()


def map_disease(img_path):
    img, masked, pred = process_all(img_path)

    if not os.path.exists(DISEASE_ROOT):
        os.mkdir(DISEASE_ROOT)

    img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    cv2.imwrite(f'{DISEASE_ROOT}image.png', img_np)

    masked_uint8 = masked
    if masked.dtype != np.uint8:
        masked_uint8 = (np.clip(masked, 0, 1) * 255).astype(np.uint8)
    cv2.imwrite(f'{DISEASE_ROOT}sclera.png', masked_uint8)

    pred_binary = (pred > 0).astype(np.uint8) * 255
    cv2.imwrite(f'{DISEASE_ROOT}vessels.png', pred_binary)

    img_bgr = cv2.imread(f'{DISEASE_ROOT}image.png') 

    model_output_sclera = cv2.imread(f'{DISEASE_ROOT}sclera.png', cv2.IMREAD_GRAYSCALE)
    model_output_vessels = cv2.imread(f'{DISEASE_ROOT}vessels.png', cv2.IMREAD_GRAYSCALE)

    results = analyze_eye_image_from_arrays(img_bgr, model_output_sclera, model_output_vessels)

    return results


if __name__ == "__main__":
    img_path = 'stages/images/test.jpg'
    stage_visualize(img_path)
    visualize(img_path)






