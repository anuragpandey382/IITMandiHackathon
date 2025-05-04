import time
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image
import torch
from matplotlib import pyplot as plt
from matplotlib import patches
from torchvision import transforms
from torch import nn, Tensor
from functools import partial
import re
from bs4 import BeautifulSoup as bs
import tokenizers as tk
import warnings
from collections import defaultdict

sys.path.append('/home/teaching/Desktop/test/down/unitable_dir/unitable')

from src.model import EncoderDecoder, ImgLinearBackbone, Encoder, Decoder
from src.utils import (
    subsequent_mask, pred_token_within_range, greedy_sampling, bbox_str_to_token_list,
    cell_str_to_token_list, html_str_to_token_list
)
from src.trainer.utils import VALID_HTML_TOKEN, VALID_BBOX_TOKEN, INVALID_CELL_TOKEN

warnings.filterwarnings('ignore')
device = torch.device("cuda:0")

MODEL_FILE_NAME = ["unitable_large_structure.pt", "unitable_large_bbox.pt", "unitable_large_content.pt"]
MODEL_DIR = Path("../down/unitable_dir/unitable/experiments/unitable_weights/")
VOCAB_DIR = Path("../down/unitable_dir/unitable/vocab")
ENHANCED_DIR = Path("./enhanced")
PAIR_DIR = Path("./pair")
HTML_DIR = Path("./html")

HTML_DIR.mkdir(parents=True, exist_ok=True)

# Model config
d_model = 768
patch_size = 16
nhead = 12
dropout = 0.2

backbone = ImgLinearBackbone(d_model=d_model, patch_size=patch_size)
encoder = Encoder(d_model=d_model, nhead=nhead, dropout=dropout, activation="gelu",
                  norm_first=True, nlayer=12, ff_ratio=4)
decoder = Decoder(d_model=d_model, nhead=nhead, dropout=dropout, activation="gelu",
                  norm_first=True, nlayer=4, ff_ratio=4)

def image_to_tensor(image: Image, size: tuple) -> Tensor:
    T = transforms.Compose([
        transforms.Resize(size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.86597056,0.88463002,0.87491087], std = [0.20686628,0.18201602,0.18485524])
    ])
    return T(image).to(device).unsqueeze(0)

def rescale_bbox(bbox, src, tgt):
    ratio = [tgt[0] / src[0], tgt[1] / src[1]] * 2
    return [[int(round(i * j)) for i, j in zip(entry, ratio)] for entry in bbox]

def autoregressive_decode(model, image, prefix, max_decode_len, eos_id, token_whitelist=None, token_blacklist=None):
    model.eval()
    with torch.no_grad():
        memory = model.encode(image)
        context = torch.tensor(prefix, dtype=torch.int32).repeat(image.shape[0], 1).to(device)

    for _ in range(max_decode_len):
        if all(eos_id in k for k in context): break
        with torch.no_grad():
            causal_mask = subsequent_mask(context.shape[1]).to(device)
            logits = model.decode(memory, context, tgt_mask=causal_mask, tgt_padding_mask = None)
            logits = model.generator(logits)[:, -1, :]
            logits = pred_token_within_range(logits, white_list=token_whitelist, black_list=token_blacklist)
            _, next_tokens = greedy_sampling(logits)
            context = torch.cat([context, next_tokens], dim=1)
    return context

def load_vocab_and_model(vocab_file, weight_file, max_seq_len):
    vocab = tk.Tokenizer.from_file(str(vocab_file))
    model = EncoderDecoder(
        backbone=backbone,
        encoder=encoder,
        decoder=decoder,
        vocab_size=vocab.get_vocab_size(),
        d_model=d_model,
        padding_idx=vocab.token_to_id("<pad>"),
        max_seq_len=max_seq_len,
        dropout=dropout,
        norm_layer=partial(nn.LayerNorm, eps=1e-6)
    )
    model.load_state_dict(torch.load(weight_file, map_location="cpu"))
    return vocab, model.to(device)

def build_table_with_empty_cells(pred_html, pred_cells, pred_bboxes):
    soup = bs(''.join(pred_html), 'html.parser')
    table = soup.find('table')
    header_row = table.find('tr') if table else None
    header_cols = []
    if header_row:
        header_cols = [th.get_text(strip=True) != '' for th in header_row.find_all('th')]

    rows = defaultdict(list)
    for idx, bbox in enumerate(pred_bboxes):
        y_center = (bbox[1] + bbox[3]) / 2
        rows[y_center].append((bbox, idx))

    sorted_rows = sorted(rows.items(), key=lambda x: x[0])
    structured_rows = [sorted(row, key=lambda x: (x[0][0] + x[0][2]) / 2) for _, row in sorted_rows]

    all_x_centers = [((bbox[0] + bbox[2]) / 2) for bbox, _ in sum(structured_rows, [])]
    all_x_centers = sorted(all_x_centers)
    col_thresh = 20
    canonical_cols = []
    for x in all_x_centers:
        if not canonical_cols or abs(x - canonical_cols[-1]) > col_thresh:
            canonical_cols.append(x)

    num_cols = len(canonical_cols)
    adjusted_col_indices = list(range(num_cols))
    if header_cols:
        header_cols = header_cols + [False] * (num_cols - len(header_cols))
        for col_idx in range(num_cols):
            if not header_cols[col_idx]:
                if col_idx > 0 and not header_cols[col_idx - 1]:
                    adjusted_col_indices[col_idx] = col_idx - 1
                elif col_idx < num_cols - 1 and not header_cols[col_idx + 1]:
                    adjusted_col_indices[col_idx] = col_idx + 1

    html_rows = ["<table>"]
    for row in structured_rows:
        row_dict = {}
        for bbox, idx in row:
            x_center = (bbox[0] + bbox[2]) / 2
            col_idx = min(range(len(canonical_cols)), key=lambda i: abs(canonical_cols[i] - x_center))
            adjusted_col = adjusted_col_indices[col_idx]
            row_dict[adjusted_col] = idx

        html_rows.append("  <tr>")
        for col in range(num_cols):
            if col in row_dict:
                content = pred_cells[row_dict[col]]
                html_rows.append(f"    <td>{content}</td>")
            else:
                html_rows.append(f"    <td></td>")
        html_rows.append("  </tr>")
    html_rows.append("</table>")
    return "\n".join(html_rows)

def process_single_image(image_path: Path):
    output_path = HTML_DIR / (image_path.stem + ".html")
    if output_path.exists():
        return

    image = Image.open(image_path).convert("RGB")
    image_size = image.size

    vocab_html, model_html = load_vocab_and_model(VOCAB_DIR / "vocab_html.json", MODEL_DIR / MODEL_FILE_NAME[0], 784)
    image_tensor = image_to_tensor(image, (448, 448))
    pred_html = autoregressive_decode(model_html, image_tensor, [vocab_html.token_to_id("[html]")], 512, vocab_html.token_to_id("<eos>"), [vocab_html.token_to_id(i) for i in VALID_HTML_TOKEN])
    pred_html_tokens = vocab_html.decode(pred_html.detach().cpu().numpy()[0], skip_special_tokens=False)
    pred_html = html_str_to_token_list(pred_html_tokens)

    vocab_bbox, model_bbox = load_vocab_and_model(VOCAB_DIR / "vocab_bbox.json", MODEL_DIR / MODEL_FILE_NAME[1], 1024)
    pred_bbox = autoregressive_decode(model_bbox, image_tensor, [vocab_bbox.token_to_id("[bbox]")], 1024, vocab_bbox.token_to_id("<eos>"), [vocab_bbox.token_to_id(i) for i in VALID_BBOX_TOKEN[:449]])
    pred_bbox = bbox_str_to_token_list(vocab_bbox.decode(pred_bbox.detach().cpu().numpy()[0], skip_special_tokens=False))
    pred_bbox = rescale_bbox(pred_bbox, (448, 448), image_size)

    vocab_cell, model_cell = load_vocab_and_model(VOCAB_DIR / "vocab_cell_6k.json", MODEL_DIR / MODEL_FILE_NAME[2], 200)
    cell_tensors = torch.cat([image_to_tensor(image.crop(b), (112, 448)) for b in pred_bbox], dim=0)
    pred_cell = autoregressive_decode(model_cell, cell_tensors, [vocab_cell.token_to_id("[cell]")], 200, vocab_cell.token_to_id("<eos>"), token_blacklist=[vocab_cell.token_to_id(i) for i in INVALID_CELL_TOKEN])
    pred_cell = vocab_cell.decode_batch(pred_cell.detach().cpu().numpy(), skip_special_tokens=False)
    pred_cell = [re.sub(r'(\d).\s+(\d)', r'\1.\2', cell_str_to_token_list(i)) for i in pred_cell]

    final_html = build_table_with_empty_cells(pred_html, pred_cell, pred_bbox)
    with open(output_path, "w") as f:
        f.write(bs(final_html, "html.parser").prettify())

    print(f"✅ Saved: {output_path.name}")

def process_all_enhanced_images():
    enhanced_images = sorted(ENHANCED_DIR.glob("*.png")) + sorted(ENHANCED_DIR.glob("*.jpg")) + sorted(ENHANCED_DIR.glob("*.jpeg"))
    if not enhanced_images:
        print("📭 No images found in 'enhanced/' to process.")
        return
    for image_path in enhanced_images:
        process_single_image(image_path)

class PairFolderEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith((".jpg", ".jpeg", ".png", ".txt")):
            print(f"\n🔔 Detected new file in 'pair/': {Path(event.src_path).name}")
            process_all_enhanced_images()

if __name__ == "__main__":
    observer = Observer()
    observer.schedule(PairFolderEventHandler(), str(PAIR_DIR), recursive=False)
    observer.start()
    print("👀 Watching for new files in ./pair ...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

