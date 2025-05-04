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

warnings.filterwarnings("ignore", category=UserWarning)


print("Setting up configuration...")
BASE_PATH = Path("../SBVPI files/SBVPI/")
TEST_PATH = Path("../test_images")
IMG_SIZE = (512, 512)
BATCH_SIZE = 2
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

  
  
  
  
def get_robust_transforms_albumentations():
    """Define more robust augmentations using Albumentation."""
    train_transform = A.Compose([
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.RandomRotate90(p=0.5),
        A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.2,
                          rotate_limit=30, p=0.7),
        A.Transpose(p=0.1),

        A.OneOf([
            A.ElasticTransform(alpha=120, sigma=120 * 0.05, alpha_affine=120 * 0.03, p=0.5),
            A.GridDistortion(p=0.5),
            A.OpticalDistortion(distort_limit=1.0, shift_limit=0.5, p=0.5),
        ], p=0.4),

        A.OneOf([
            A.CLAHE(clip_limit=4.0, tile_grid_size=(8, 8), p=0.5),
            A.RandomBrightnessContrast(brightness_limit=0.4, contrast_limit=0.4, p=0.5),
            A.RandomGamma(gamma_limit=(70, 130), p=0.5),
            A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=15, val_shift_limit=10, p=0.3),
        ], p=0.7),

        A.OneOf([
            A.Blur(blur_limit=5, p=0.5),
            A.MedianBlur(blur_limit=5, p=0.5),
            A.GaussianBlur(blur_limit=5, p=0.5),
            A.MotionBlur(blur_limit=5, p=0.3),
        ], p=0.4),

        A.OneOf([
            A.GaussNoise(var_limit=(10.0, 70.0), p=0.5),
            A.MultiplicativeNoise(multiplier=[0.8, 1.2], per_channel=True, p=0.5),
            A.ISONoise(color_shift=(0.01, 0.05), intensity=(0.1, 0.5), p=0.3),
        ], p=0.4),

    ])
    return train_transform


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

            pred = learn.model(img_t_aug)

              
            if pred.shape[0] == 1:
                pred = pred.squeeze(0)

            pred = inverse_transform(pred)

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
    global learn

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


          
          
        dls = temp_vein_block.dataloaders(BASE_PATH if dummy_files[0].parent.exists() else dummy_files, bs=BATCH_SIZE, path=Path('.'), shuffle=False, drop_last=False)

          
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
                  
                try:
                    # Load the model weights
                    learn.model.load_state_dict(torch.load(loaded_model_path))
                    print("Model weights (.pth) loaded successfully.")
                    
                    # Add this line to move the model to GPU
                    learn.model = learn.model.cuda()
                    print("Model moved to CUDA device.")
                except Exception as e:
                    print(f"Error loading model weights from .pth: {e}")
                    print("Falling back to attempting to load the .pkl file.")
                    loaded_model_path = None
            except Exception as e:
                 print(f"Error loading model weights from .pth: {e}")
                 print("Falling back to attempting to load the .pkl file.")
                 loaded_model_path = None   


        if loaded_model_path is None or not BEST_MODEL_WEIGHTS_PATH.exists():   
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
          


        print("\nShowing validation results...")
        try:
            learn.show_results(max_n=4, figsize=(15, 10))
            if 'ipykernel' not in sys.modules:
                 plt.show()
        except Exception as e:
            print(f"Could not show results: {e}")


    test_files = list(TEST_PATH.glob("*.jpg")) + list(TEST_PATH.glob("*.jpeg")) + list(TEST_PATH.glob("*.png")) + list(TEST_PATH.glob("*.JPG"))

    if test_files:
          
        if 'learn' in globals() and learn is not None:
            enhanced_batch_predict_fastai(learn, test_files)
        else:
            print("ERROR: Model was not loaded successfully. Cannot perform prediction.")
    else:
        print(f"No test images found in {TEST_PATH}")


if __name__ == "__main__":
    print("=" * 80)
    print("Enhanced Eye Vessel Segmentation with U-Net")
    print("=" * 80)
    print("Usage modes:")
    print("  1. Training + Prediction: python your_script_name.py")
    print("  2. Prediction only:       python your_script_name.py --predict-only")
    print("=" * 80)

    main()

