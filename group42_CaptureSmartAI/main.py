import os
import torch
import matplotlib.pyplot as plt
from torch import optim, nn
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
from tqdm import tqdm
from dataloaders import create_dataloaders
import timm

class EfficientNetRegressionModel(nn.Module):
    def __init__(self):
        super().__init__()

        # EfficientNet-Lite0 as feature extractor
        self.feature_extractor = timm.create_model('efficientnet_lite0', pretrained=True, num_classes=0)

        # Output is already [B, 1280]
        self.layer_norm = nn.LayerNorm(1280)

        self.fnn = nn.Sequential(
            nn.Linear(1280, 128),
            nn.ReLU()
        )

        self.head_ss_var  = nn.Linear(128, 1)
        self.head_iso_var = nn.Linear(128, 1)

    def forward(self, x):
        x = self.feature_extractor(x)  # [B, 1280]
        x = self.layer_norm(x)
        x = self.fnn(x)
        return self.head_ss_var(x), self.head_iso_var(x)


def print_parameters(model):
    total_params = sum(p.numel() for p in model.parameters())  # Count total parameters
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)  # Count only trainable parameters
    print(f"Total parameters: {total_params}")
    print(f"Trainable parameters: {trainable_params}")



def plot_loss_history(epochs, train_ss, train_iso, test_ss, test_iso, save_prefix="results"):
    """
    Plot separate loss curves for SS_var and ISO_var.

    Args:
        epochs (int): Number of training epochs.
        train_ss (list or array): Training SS_var losses.
        test_ss (list or array): Testing SS_var losses.
        train_iso (list or array): Training ISO_var losses.
        test_iso (list or array): Testing ISO_var losses.
        save_prefix (str, optional): If provided, saves figures as '{save_prefix}_ss.png' and '{save_prefix}_iso.png'.
    """
    # Plot SS_var
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, epochs + 1), train_ss, label="Train SS_var")
    plt.plot(range(1, epochs + 1), test_ss,  label="Test SS_var")
    plt.title("SS_var MAE Loss over Epochs")
    plt.xlabel("Epoch")
    plt.ylabel("MAE Loss")
    plt.legend()
    plt.grid(True)
    if save_prefix:
        plt.savefig(f"{save_prefix}_ss.png", bbox_inches='tight')
    plt.show()

    # Plot ISO_var
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, epochs + 1), train_iso, label="Train ISO_var")
    plt.plot(range(1, epochs + 1), test_iso,  label="Test ISO_var")
    plt.title("ISO_var MAE Loss over Epochs")
    plt.xlabel("Epoch")
    plt.ylabel("MAE Loss")
    plt.legend()
    plt.grid(True)
    if save_prefix:
        plt.savefig(f"{save_prefix}_iso.png", bbox_inches='tight')
    plt.show()



def train():
    # Paths
    IMG_DIR    = "videos/frames/"
    LABEL_FILE = os.path.join(IMG_DIR, "frame_labels.csv")

    # Hyperparams
    BS     = 32
    EPOCHS = 100
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Data
    train_loader, val_loader = create_dataloaders(
        images_dir=IMG_DIR, labels_csv=LABEL_FILE, batch_size=BS
    )

    # Model, loss, optimizer, scheduler
    model     = EfficientNetRegressionModel().to(DEVICE)
    criterion = nn.L1Loss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-5)

    print_parameters(model)

    # Histories
    train_ss_hist, train_iso_hist = [], []
    test_ss_hist,  test_iso_hist  = [], []

    best_test_ss_loss = float("inf")
    best_model_path = "/home/teaching/G42/Hack/best_model_ss_new.pth"

    for epoch in tqdm(range(1, EPOCHS + 1)):
        model.train()
        ss_loss_train, iso_loss_train = 0.0, 0.0

        for images, labels in train_loader:
            images = images.to(DEVICE)
            ss_gt  = labels['SS_var'].float().view(-1,1).to(DEVICE)
            iso_gt = labels['ISO_var'].float().view(-1,1).to(DEVICE)

            optimizer.zero_grad()
            ss_pred, iso_pred = model(images)
            loss = criterion(ss_pred, ss_gt) + criterion(iso_pred, iso_gt)
            loss.backward()
            optimizer.step()

            ss_loss_train  += criterion(ss_pred, ss_gt).item()
            iso_loss_train += criterion(iso_pred, iso_gt).item()

        train_ss_hist .append(ss_loss_train  / len(train_loader))
        train_iso_hist.append(iso_loss_train / len(train_loader))

        model.eval()
        ss_loss_test, iso_loss_test = 0.0, 0.0
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(DEVICE)
                ss_gt  = labels['SS_var'].float().view(-1,1).to(DEVICE)
                iso_gt = labels['ISO_var'].float().view(-1,1).to(DEVICE)
                ss_pred, iso_pred = model(images)
                ss_loss_test  += criterion(ss_pred, ss_gt).item()
                iso_loss_test += criterion(iso_pred, iso_gt).item()

        avg_ss_test_loss = ss_loss_test / len(val_loader)
        test_ss_hist .append(ss_loss_test  / len(val_loader))
        test_iso_hist.append(iso_loss_test / len(val_loader))
        scheduler.step()

        print(f"Epoch {epoch}/{EPOCHS}  "
              f"Train [SS: {train_ss_hist[-1]:.4f}, ISO: {train_iso_hist[-1]:.4f}]  "
              f"Test [SS: {test_ss_hist[-1]:.4f}, ISO: {test_iso_hist[-1]:.4f}]")

        if avg_ss_test_loss < best_test_ss_loss:
            best_test_ss_loss = avg_ss_test_loss
            torch.save(model.state_dict(), best_model_path)

    plot_loss_history(epochs=EPOCHS, train_ss=train_ss_hist, train_iso=train_iso_hist, test_ss=test_ss_hist, test_iso=test_iso_hist)


if __name__ == "__main__":
    train()

