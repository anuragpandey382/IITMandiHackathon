"""
    TRYING TO IMPROVE PART-2
    Modified to also save model weights as .pth file using torch.save,
    and save the MinMaxScaler and KMeans model using joblib.
    Fixed CUDA/CPU mismatch error during prediction.
"""

import torch
from fastai.vision.all import *
import cv2
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image as PILImage_module
import warnings
import sys
from tqdm.auto import tqdm
import pickle
import math
import albumentations as A  
from sklearn.cluster import KMeans  
from sklearn.preprocessing import MinMaxScaler  
import joblib  
from skimage import morphology  
from scipy.ndimage import distance_transform_edt  
from scipy.special import softmax  
from collections import Counter  
from multiprocessing import Pool  

warnings.filterwarnings("ignore", category=UserWarning)


print("Setting up configuration...")
BASE_PATH = Path("../SBVPI files/SBVPI/")
TEST_PATH = Path("../test_images")
IMG_SIZE = (1024,1024)
BATCH_SIZE = 1
EPOCHS = 30
MASK_SUFFIX = "_vessels.png"
MODEL_DIR = Path("./models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)  
PREDICTIONS_DIR = Path("./predictions")
PREDICTIONS_DIR.mkdir(exist_ok=True)

DEBUG_PREDS_DIR = Path("./debug_predictions")
DEBUG_PREDS_DIR.mkdir(exist_ok=True)

BEST_MODEL_WEIGHTS_PATH = MODEL_DIR / 'bestmodel.pth'
FINAL_MODEL_STATE_PATH = MODEL_DIR / 'vessel_segmentation_model_final.pkl'

 
SCALER_PATH = MODEL_DIR / 'scaler.joblib'
KMEANS_PATH = MODEL_DIR / 'kmeans.joblib'
 

 
def skeletonize_image(binary_image):
     
    return morphology.skeletonize(binary_image.astype(bool))

def find_branch_points(skel):
     
    skel_uint8 = skel.astype(np.uint8)
    branch_points = 0
    for i in range(1, skel_uint8.shape[0]-1):
        for j in range(1, skel_uint8.shape[1]-1):
            if skel_uint8[i, j] == 1:
                 
                neighborhood_sum = np.sum(skel_uint8[i-1:i+2, j-1:j+2]) - skel_uint8[i, j]
                 
                if neighborhood_sum > 3:
                    branch_points += 1
    return branch_points


def find_endpoints(skel):
     
    skel_uint8 = skel.astype(np.uint8)
    endpoints = 0
    for i in range(1, skel_uint8.shape[0]-1):
        for j in range(1, skel_uint8.shape[1]-1):
            if skel_uint8[i, j] == 1:
                 
                neighborhood_sum = np.sum(skel_uint8[i-1:i+2, j-1:j+2]) - skel_uint8[i, j]
                 
                if neighborhood_sum == 2:
                    endpoints += 1
    return endpoints


 
initial_weights = np.array([2.5, 2.0, 1.5, 3.25, 2.0, 1.0])
softmax_weights = softmax(initial_weights)

def extract_raw_features(image_path_and_name_tuple, resize_shape=(512, 512)):
    image_path, fname = image_path_and_name_tuple
     
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"❌ Cannot read: {image_path}")
        return None

     
    _, binary = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)

     
    resized_binary = cv2.resize(binary, resize_shape, interpolation=cv2.INTER_NEAREST)  

     
    resized_binary = (resized_binary > 0).astype(np.uint8) * 255


    skel = skeletonize_image(resized_binary)

    vein_length = np.sum(skel)  
     
    dist = distance_transform_edt(resized_binary // 255)
    vein_width = np.mean(dist[resized_binary == 255]) if np.any(resized_binary == 255) else 0
    density = np.sum(resized_binary == 255) / resized_binary.size
    bp = find_branch_points(skel)
    ep = find_endpoints(skel)

     
    coords = np.column_stack(np.where(skel))
    tortuosity = vein_length / np.linalg.norm(coords[0] - coords[-1]) if len(coords) >= 2 else 1.0

     
    raw = np.array([density, bp, ep, tortuosity, vein_length, vein_width])
    return [fname, raw]

 


def robust_image_preprocess(img_path, target_size=IMG_SIZE):
    """
    Preprocess images consistently regardless of original size or properties.
    (Note: For training/fastai prediction, use the DataBlock transforms instead)
    """
    if isinstance(img_path, (str, Path)):
        img = cv2.imread(str(img_path))
        if img is None:
            raise ValueError(f"Could not read image at {img_path}")
    else:
        img = np.array(img_path)
        if len(img.shape) == 3 and img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(10, 10))
    l_clahe = clahe.apply(l)

    l_enhanced = l_clahe  

    lab_enhanced = cv2.merge((l_enhanced, a, b))
    img_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    img_gray = cv2.cvtColor(img_enhanced, cv2.COLOR_BGR2GRAY)
    processed = cv2.merge([img_gray, img_gray, img_gray])

    resized = cv2.resize(processed, target_size, interpolation=cv2.INTER_AREA)

    processed_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    return processed_rgb


def get_all_image_files(path):
    """Find all valid image files that have corresponding vessel mask files."""
    files = []

    print(f"Scanning for image-mask pairs in {path}...")
    all_images = get_image_files(path, recurse=True, folders=None)

    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    all_images = [f for f in all_images if f.suffix.lower() in valid_exts]

    for img_file in all_images:
        if MASK_SUFFIX not in img_file.name and \
           "_sclera" not in img_file.name and \
           "_periocular" not in img_file.name and \
           "_canthus" not in img_file.name and \
           "_iris" not in img_file.name and \
           "_pupil" not in img_file.name and \
           "_eyelashes" not in img_file.name and \
           "_pred" not in img_file.name:

            mask_file = img_file.parent / f"{img_file.stem}{MASK_SUFFIX}"
            if mask_file.exists():
                files.append(img_file)

    print(f"Found {len(files)} images with corresponding '{MASK_SUFFIX}' masks.")

    if not files:
        print("WARNING: No valid image-mask pairs found for training!")
    return files

def get_mask_path(img_path):
    """Get the corresponding mask path for an image file."""
    return img_path.parent / f"{img_path.stem}{MASK_SUFFIX}"

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

        clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=self.tile_grid_size)
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

def fix_masks(base_path, mask_suffix="_vessels.png"):
    """Verify and fix masks to ensure binary 0/1 values."""
    all_mask_files = list(base_path.glob(f"**/*{mask_suffix}"))
    print(f"Checking {len(all_mask_files)} mask files...")

    fixed_count = 0
    for mask_path in all_mask_files:
        try:
            with PILImage_module.open(mask_path) as mask_img:
                if mask_img.mode != 'L':
                    mask_img = mask_img.convert('L')
                mask_array = np.array(mask_img)

            unique_values = np.unique(mask_array)
            if not (np.all(np.isin(unique_values, [0, 1]))):
                 binary_mask = (mask_array > 0).astype(np.uint8)
                 PILImage_module.fromarray(binary_mask, mode='L').save(mask_path)
                 fixed_count += 1

        except Exception as e:
            print(f"Error with mask {mask_path}: {e}")

    print(f"Fixed {fixed_count} masks to binary 0/1 format.")

def dice_vessel(inp, targ, smooth=1e-6):
    """Dice coefficient metric for vessel segmentation."""
    inp = (inp.sigmoid() > 0.5).float()
    targ = targ.float()
    intersection = (inp * targ).sum()
    return (2. * intersection + smooth) / (inp.sum() + targ.sum() + smooth)

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


def predict_with_tta(learn, img, n_augments=5):
    """
    Perform test-time augmentation for more robust predictions.
    """
    tta_transforms = [
        lambda x: x,  
        lambda x: torch.flip(x, dims=[-1]),  
        lambda x: torch.flip(x, dims=[-2]),  
        lambda x: torch.rot90(x, k=1, dims=[-2, -1]),  
        lambda x: torch.rot90(x, k=2, dims=[-2, -1]),  
    ]

    inverse_transforms = [
        lambda x: x,  
        lambda x: torch.flip(x, dims=[-1]),  
        lambda x: torch.flip(x, dims=[-2]),  
        lambda x: torch.rot90(x, k=3, dims=[-2, -1]),  
        lambda x: torch.rot90(x, k=2, dims=[-2, -1]),  
    ]

    if isinstance(img, (str, Path)):
        img = PILImage.create(img)

    preds = []

     
    test_dl_single = learn.dls.test_dl([img])
    x = test_dl_single.one_batch()[0]  

    for i in range(min(n_augments, len(tta_transforms))):
        transform = tta_transforms[i]
        inverse_transform = inverse_transforms[i]

        with torch.no_grad():
            img_t_aug = transform(x)

             
            if img_t_aug.ndim == 3:
                img_t_aug = img_t_aug.unsqueeze(0)

             
             
            if learn.model.parameters().__next__().is_cuda:  
                  
                 img_t_aug = img_t_aug.cuda()
            else:
                  
                 img_t_aug = img_t_aug.cpu()
             


            pred = learn.model(img_t_aug)

             
            if pred.shape[0] == 1:
                pred = pred.squeeze(0)

             
            pred = inverse_transform(pred).cpu()
             

            preds.append(pred)

    final_pred_logits = torch.stack(preds).mean(dim=0)

     
     
     
    avg_probs = torch.sigmoid(final_pred_logits)
    return (avg_probs, final_pred_logits, avg_probs)  


def enhanced_batch_predict_fastai(learn, test_files):
    """
    Process all test images using the fastai pipeline for consistent preprocessing.
    """
    output_dir = PREDICTIONS_DIR
    output_dir.mkdir(exist_ok=True)
    debug_dir = DEBUG_PREDS_DIR
    debug_dir.mkdir(exist_ok=True)


    print(f"Processing {len(test_files)} test images using fastai pipeline...")

    results = []
    for img_path in tqdm(test_files, desc="Predicting with TTA"):
         try:
              
             pred_probs_tensor, raw_logits, avg_probs = predict_with_tta(learn, img_path)

              
             pred_probs_np = avg_probs.cpu().numpy().squeeze()

              
             debug_prob_img = (pred_probs_np * 255).astype(np.uint8)
             debug_out_path = debug_dir / f"{img_path.stem}_prob_map.png"
             PILImage_module.fromarray(debug_prob_img, mode='L').save(debug_out_path)

              
             binary_mask_np = (pred_probs_np > 0.2).astype(np.uint8)  

              
             num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_mask_np, connectivity=8)

             min_size = 5
             clean_mask = np.zeros_like(binary_mask_np)
             if num_labels > 1:
                 for j in range(1, num_labels):
                     if stats[j, cv2.CC_STAT_AREA] >= min_size:
                         clean_mask[labels == j] = 1

              
             kernel = np.ones((3, 3), np.uint8)
             clean_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_CLOSE, kernel)

             binary_pred_saved = clean_mask.astype(np.uint8) * 255

             out_path = output_dir / f"{img_path.stem}_pred.png"
             PILImage_module.fromarray(binary_pred_saved, mode='L').save(out_path)

             vessel_pixels = clean_mask.sum()
             total_pixels = clean_mask.size
             vessel_density = vessel_pixels / total_pixels if total_pixels > 0 else 0

             results.append({
                 'image': img_path.name,
                 'vessel_density': vessel_density,
                 'output_path': out_path
             })

         except Exception as e:
             print(f"Error processing prediction for {img_path.name}: {e}")
             import traceback
             traceback.print_exc()


    print("\nProcessing complete!")
    print(f"Saved {len(results)} predictions to {output_dir}")
    print(f"Raw probability maps saved to {debug_dir} for debugging.")

    if results:
        print("\nVessel Density Summary:")
        for i, res in enumerate(results):
            print(f"{i+1}. {res['image']}: {res['vessel_density']:.4f}")

        if results:
            avg_density = sum(r['vessel_density'] for r in results) / len(results)
            print(f"\nAverage vessel density: {avg_density:.4f}")


def main():
    global learn, scaler, kmeans  

    skip_training = False
    if len(sys.argv) > 1 and sys.argv[1].lower() == '--predict-only':
        skip_training = True
        print("Skipping training, prediction mode only...")

         
         
        print("Defining model architecture for loading...")
         
         
        temp_vein_block = DataBlock(
            blocks=(ImageBlock, MaskBlock(codes=['background', 'vessel'])),
            get_items=get_all_image_files,  
            splitter=RandomSplitter(valid_pct=0.2, seed=42),
            get_y=get_mask_path,
            item_tfms=[
                AdvancedVesselPreprocessing(clip_limit=4.0, tile_grid_size=(10, 10)),
                Resize(IMG_SIZE, method='squish')
            ],
            batch_tfms=[
                Normalize.from_stats(*imagenet_stats),
            ]
        )

         
         
        dummy_files = get_all_image_files(BASE_PATH)
        if not dummy_files:
             print("Warning: No training files found. Creating minimal dummy file list for dataloader structure.")
              
              
              
             dummy_files = [Path("dummy_image.jpg")]


         
         
        dls = temp_vein_block.dataloaders(BASE_PATH if dummy_files and dummy_files[0].parent.exists() else dummy_files, bs=BATCH_SIZE, path=Path('.'), shuffle=False, drop_last=False)


         
        learn = unet_learner(
            dls,
            resnet34,  
            n_out=1,
            metrics=[dice_vessel],  
            loss_func=EnhancedSegmentationLoss(),
            wd=1e-2,
            path=Path('.'),
            model_dir=MODEL_DIR.relative_to(Path('.')),
            self_attention=True  
        )
        print("Learner architecture defined.")

         
        loaded_model_path = None
         
        if BEST_MODEL_WEIGHTS_PATH.exists():
            loaded_model_path = BEST_MODEL_WEIGHTS_PATH
            print(f"Attempting to load model weights from {loaded_model_path}...")
            try:
                 
                 
                 
                learn.model.load_state_dict(torch.load(loaded_model_path, map_location=torch.device('cpu')))
                print("Model weights (.pth) loaded successfully.")
            except Exception as e:
                 print(f"Error loading model weights from .pth: {e}")
                 print("Falling back to attempting to load the .pkl file.")
                 loaded_model_path = None  


        if loaded_model_path is None or (loaded_model_path.suffix == '.pth' and not BEST_MODEL_WEIGHTS_PATH.exists()):  
            model_paths_pkl = [FINAL_MODEL_STATE_PATH, MODEL_DIR / 'vessel_segmentation_model.pkl']
            for mp in model_paths_pkl:
                if mp.exists():
                    loaded_model_path = mp
                    break

            if loaded_model_path is None:
                print(f"ERROR: No model file (.pth or .pkl) found in {MODEL_DIR}. Looked for: {BEST_MODEL_WEIGHTS_PATH}, {', '.join([str(p) for p in model_paths_pkl])}")
                print("You must train the model first or provide a valid model file.")
                return

            print(f"Loading complete learner state from {loaded_model_path}...")
            try:
                 
                 
                learn = load_learner(loaded_model_path, cpu=False, pickle_module=pickle)
                print("Model state (.pkl) loaded successfully.")
            except Exception as e:
                print(f"Error loading learner state: {e}")
                print("Please ensure the fastai version and pickle module are compatible.")
                if "AttributeError: Can't get attribute" in str(e):
                    print("This might be due to changes in class definitions between saving and loading.")
                    print("Ensure your code (especially custom classes like EnhancedSegmentationLoss, AdvancedVesselPreprocessing) is the same version.")
                return
         

         
        print("Loading Scaler and KMeans models...")
        try:
            if SCALER_PATH.exists():
                scaler = joblib.load(SCALER_PATH)
                print(f"Scaler loaded from {SCALER_PATH}")
            else:
                print(f"WARNING: Scaler not found at {SCALER_PATH}. Feature normalization will not be performed.")
                scaler = None  

            if KMEANS_PATH.exists():
                kmeans = joblib.load(KMEANS_PATH)
                print(f"KMeans model loaded from {KMEANS_PATH}")
            else:
                print(f"WARNING: KMeans model not found at {KMEANS_PATH}. Clustering prediction will not be performed.")
                kmeans = None  

        except Exception as e:
             print(f"Error loading scaler or kmeans models: {e}")
             scaler = None
             kmeans = None
         


    if not skip_training:
        fix_masks(BASE_PATH, MASK_SUFFIX)

        vein_block = DataBlock(
            blocks=(ImageBlock, MaskBlock(codes=['background', 'vessel'])),
            get_items=get_all_image_files,
            splitter=RandomSplitter(valid_pct=0.2, seed=42),
            get_y=get_mask_path,
            item_tfms=[
                AdvancedVesselPreprocessing(clip_limit=4.0, tile_grid_size=(10, 10)),
                Resize(IMG_SIZE, method='squish')
            ],
            batch_tfms=[
                 
                *aug_transforms(
                    size=IMG_SIZE,
                    mult=2.0,
                    max_rotate=30.0,
                    flip_vert=True,
                    max_lighting=0.3,
                    max_zoom=1.4,
                    max_warp=0.3,
                    p_affine=0.75,
                    p_lighting=0.6,
                ),
                Normalize.from_stats(*imagenet_stats),
            ]
        )

        print(f"Creating DataLoaders from: {BASE_PATH}")
        dls = vein_block.dataloaders(BASE_PATH, bs=BATCH_SIZE, path=Path('.'))
        print(f"DataLoaders: {len(dls.train_ds)} training, {len(dls.valid_ds)} validation items")

        print("Showing sample batch...")
        try:
            dls.show_batch(max_n=4, figsize=(10, 8))
            if 'ipykernel' not in sys.modules:
                 plt.show()
        except Exception as e:
            print(f"Could not show batch: {e}")


        learn = unet_learner(
            dls,
            resnet34,
            n_out=1,
            metrics=[dice_vessel],
            loss_func=EnhancedSegmentationLoss(dice_weight=0.7, bce_weight=0.15, focal_weight=0.15),
            wd=1e-2,
            path=Path('.'),
            model_dir=MODEL_DIR.relative_to(Path('.')),
            self_attention=True
        )

        print("Finding optimal learning rate...")
        try:
            with warnings.catch_warnings():
               warnings.simplefilter("ignore", UserWarning)
               lr_find_res = learn.lr_find(num_it=100)
            suggested_lr = lr_find_res.valley if hasattr(lr_find_res, 'valley') and lr_find_res.valley is not None else 1e-3
            print(f"Suggested learning rate: {suggested_lr:.2e}")
             
             
             
             

        except Exception as lr_e:
            print(f"Error during learning rate find: {lr_e}. Using default LR 1e-3.")
            suggested_lr = 1e-3


        print(f"Training for {EPOCHS} epochs with progressive phases...")

        learn.freeze()
        print("Phase 1: Training head...")
        learn.fit_one_cycle(7, suggested_lr)

        learn.unfreeze()
        print("\nPhase 2: Fine-tuning...")
        learn.fit_one_cycle(
            13,
            lr_max=slice(suggested_lr/10, suggested_lr/2),
            cbs=[
                GradientClip(0.1),
                GradientAccumulation(2),
            ]
        )

        print("\nPhase 3: Final fine-tuning with Early Stopping...")
        learn.fit_one_cycle(
            EPOCHS-20,
            lr_max=slice(suggested_lr/100, suggested_lr/10),
            cbs=[
                GradientClip(0.1),
                GradientAccumulation(2),
                EarlyStoppingCallback(monitor='dice_vessel', min_delta=0.001, patience=10)
            ]
        )

        print("\nSaving model...")
         
        learn.export(FINAL_MODEL_STATE_PATH)
        print(f"Final model state saved to {FINAL_MODEL_STATE_PATH}")

         
        try:
             
            BEST_MODEL_WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
            torch.save(learn.model.state_dict(), BEST_MODEL_WEIGHTS_PATH)
            print(f"Model weights (state_dict) saved to {BEST_MODEL_WEIGHTS_PATH}")
        except Exception as e:
            print(f"Error saving model weights using torch.save: {e}")
         

         
        print("\nTraining and Saving Scaler and KMeans models...")
        try:
             
            feature_dataset_path = "/home/teaching/scelar/SBVPI files original/SBVPI"  
            image_info_list = [
                (os.path.join(root, fname), fname)
                for root, _, files in os.walk(feature_dataset_path)
                for fname in files if fname.endswith("_vessels.png")  
            ]
            print(f"🔍 Found {len(image_info_list)} mask images for feature training")

            if not image_info_list:
                 print("WARNING: No mask files found for training scaler and kmeans. Skipping.")
            else:
                 
                with Pool(16) as pool:
                    raw_results = list(tqdm(pool.imap_unordered(extract_raw_features, image_info_list),
                                            total=len(image_info_list), desc="⚙️ Extracting raw features for scaler/kmeans"))

                raw_results = [r for r in raw_results if r]
                raw_features = np.array([r[1] for r in raw_results])

                 
                scaler = MinMaxScaler()
                scaler.fit(raw_features)
                joblib.dump(scaler, SCALER_PATH)
                print(f"Scaler trained and saved to {SCALER_PATH}")

                 
                normalized_features = scaler.transform(raw_features)
                weighted_features = normalized_features * softmax_weights

                 
                kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)  
                kmeans.fit(weighted_features)
                joblib.dump(kmeans, KMEANS_PATH)
                print(f"KMeans model trained (2 clusters) and saved to {KMEANS_PATH}")

                 
                labels = kmeans.predict(weighted_features)
                cluster_counts = Counter(labels)
                print(f"\n📦 Training Data Cluster Distribution:")
                for cluster_id in range(2):
                    print(f"  Cluster {cluster_id} → {cluster_counts[cluster_id]} images")

        except Exception as e:
            print(f"Error training or saving scaler/kmeans models: {e}")
         


        print("\nShowing validation results...")
        try:
            learn.show_results(max_n=4, figsize=(15, 10))
            if 'ipykernel' not in sys.modules:
                 plt.show()
        except Exception as e:
            print(f"Could not show results: {e}")


    test_files = list(TEST_PATH.glob("*.jpg")) + list(TEST_PATH.glob("*.jpeg")) + list(TEST_PATH.glob("*.png"))

    if test_files:
         
        if 'learn' in globals() and learn is not None:
             
            if 'scaler' not in globals() or scaler is None or 'kmeans' not in globals() or kmeans is None:
                 print("WARNING: Scaler or KMeans models not loaded. Skipping batch prediction with clustering.")
                  
                  
                  
                 pass  
            else:
                  
                  
                 enhanced_batch_predict_fastai(learn, test_files)
             

        else:
            print("ERROR: Model was not loaded successfully. Cannot perform prediction.")
    else:
        print(f"No test images found in {TEST_PATH}")


if __name__ == "__main__":
    print("=" * 80)
    print("Enhanced Eye Vessel Segmentation and Feature Extraction Training")
    print("=" * 80)
    print("Usage modes:")
    print("  1. Training + Prediction + Feature Model Training: python your_script_name.py")
    print("  2. Prediction only:       python your_script_name.py --predict-only")
    print("=" * 80)

     
    try:
        import joblib
    except ImportError:
        print("Error: joblib is not installed. Please install it using 'pip install joblib'")
        sys.exit(1)
     

    main()

