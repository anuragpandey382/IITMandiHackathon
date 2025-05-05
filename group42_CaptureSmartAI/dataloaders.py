import os
import pandas as pd
from sklearn.model_selection import train_test_split
from PIL import Image
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms

class ImageDataset(Dataset):
    """
    Custom PyTorch Dataset to load images and their corresponding labels.
    """

    def __init__(self, image_paths, labels, transform=None):
        """
        Args:
            image_paths (list): List of image file paths.
            labels (DataFrame): Pandas DataFrame containing labels.
            transform (callable, optional): Optional transform to be applied on a sample.
        """
        self.image_paths = image_paths
        self.labels = labels.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        # Load image
        img_path = self.image_paths[idx]
        image = Image.open(img_path)

        # Resize to (224, 224)
        image = image.resize((224, 224))
        # Convert to grayscale then replicate to 3 channels
        image = image.convert("L")
        image = Image.merge("RGB", (image, image, image))

        # Apply transforms if given
        if self.transform:
            image = self.transform(image)

        # Fetch labels
        label_row = self.labels.iloc[idx]
        label = {
            "SS_var": label_row["SS_var"],
            "ISO_var": label_row["ISO_var"]
        }

        return image, label


def create_dataloaders(images_dir,
                       labels_csv,
                       batch_size=8,
                       test_size=0.2,
                       random_state=42):
    """
    Load images and labels, split into train/test, and create DataLoaders.
    """
    # 1. Load labels
    labels_df = pd.read_csv(labels_csv)

    # 2. Build full image paths, avoiding double ".jpg"
    def make_path(img_name):
        if img_name.lower().endswith('.jpg'):
            filename = img_name
        else:
            filename = f"{img_name}.jpg"
        return os.path.join(images_dir, filename)

    labels_df["image_path"] = labels_df["image_name"].apply(make_path)

    # 3. Filter out missing files
    valid_df = labels_df[labels_df["image_path"].apply(os.path.exists)]
    if valid_df.empty:
        raise FileNotFoundError(
            f"No valid image files found in {images_dir}. "
            "Ensure that the images and labels match."
        )

    # 4. Split into train/test
    train_df, test_df = train_test_split(
        valid_df, test_size=test_size, random_state=random_state
    )

    # 5. Define transforms
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5,0.5,0.5], std=[0.5,0.5,0.5])
    ])

    # 6. Create Dataset objects
    train_dataset = ImageDataset(
        train_df["image_path"].tolist(), train_df, transform=transform
    )

    test_dataset = ImageDataset(
        test_df["image_path"].tolist(), test_df, transform=transform
    )

    # 7. Create DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4)
    val_loader  = DataLoader(test_dataset,  batch_size=batch_size, shuffle=False, num_workers=4)
    return train_loader, val_loader

