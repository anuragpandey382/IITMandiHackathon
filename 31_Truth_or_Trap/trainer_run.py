import os
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm

def trainer(model, loader, extract_embedding_batch, args):
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.BCEWithLogitsLoss()
    epoch_loss_history = []
    os.makedirs(args.ckpt, exist_ok=True)

    # ---------- Training Loop ----------
    print("Training started")
    for epoch in range(args.num_epochs):
        model.train()
        total_loss = 0.0
        print(f"Epoch {epoch+1} started")
        
        for x, y in tqdm(loader, desc=f"Epoch {epoch+1}"):
            x, y = x.to(args.device), y.float().to(args.device)

            embs = extract_embedding_batch(x)
            logits = model(embs)
            loss = criterion(logits, y)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        epoch_loss_history.append(avg_loss)
        print(f"Epoch {epoch+1}, Loss = {avg_loss:.4f}")

        # Save checkpoint every 5 epochs
        if (epoch + 1) % 5 == 0:
            ckpt_path = os.path.join(args.ckpt, f"classifier_epoch_{epoch+1}.pt")
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': avg_loss
            }, ckpt_path)
            print(f"Checkpoint saved at {ckpt_path}")

        # Early stopping
        if len(epoch_loss_history) > 4:
            if epoch_loss_history[-4] - avg_loss < 1e-4:
                ckpt_path = os.path.join(args.ckpt, f"earlystop_epoch_{epoch+1}.pt")
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'loss': avg_loss
                }, ckpt_path)
                print(f"Early stopping triggered. Saved at {ckpt_path}")
                break
