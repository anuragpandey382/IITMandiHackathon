from pathlib import Path
from PIL import Image
import torch, re, tokenizers as tk
from bs4 import BeautifulSoup as bs
from src.model import EncoderDecoder, ImgLinearBackbone, Encoder, Decoder
from src.utils import (subsequent_mask, pred_token_within_range, greedy_sampling,
                       bbox_str_to_token_list, cell_str_to_token_list, html_str_to_token_list)
from src.trainer.utils import VALID_HTML_TOKEN, VALID_BBOX_TOKEN, INVALID_CELL_TOKEN
from torchvision import transforms
from torch import nn
from functools import partial
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')
device = torch.device("cuda:0")

# === Config ===
MODEL_FILE_NAME = ["unitable_large_structure.pt", "unitable_large_bbox.pt", "unitable_large_content.pt"]
MODEL_DIR = Path("../unitable/experiments/unitable_weights/")
input_dir = Path("~/acc/pubtabnet/train").expanduser()
output_base = Path("~/acc/pubtabnet/htmlPairsTest").expanduser()
output_base.mkdir(parents=True, exist_ok=True)

# === Model setup ===
d_model = 768
patch_size = 16
nhead = 12
dropout = 0.2

backbone = ImgLinearBackbone(d_model=d_model, patch_size=patch_size)
encoder = Encoder(d_model=d_model, nhead=nhead, dropout=dropout, activation="gelu",
                  norm_first=True, nlayer=12, ff_ratio=4)
decoder = Decoder(d_model=d_model, nhead=nhead, dropout=dropout, activation="gelu",
                  norm_first=True, nlayer=4, ff_ratio=4)

def load_vocab_and_model(vocab_path, max_seq_len, model_weights):
    vocab = tk.Tokenizer.from_file(str(vocab_path))
    model = EncoderDecoder(
        backbone=backbone, encoder=encoder, decoder=decoder,
        vocab_size=vocab.get_vocab_size(),
        d_model=d_model, padding_idx=vocab.token_to_id("<pad>"),
        max_seq_len=max_seq_len, dropout=dropout,
        norm_layer=partial(nn.LayerNorm, eps=1e-6)
    )
    model.load_state_dict(torch.load(model_weights, map_location="cpu"))
    return vocab, model.to(device)

def image_to_tensor(image, size):
    T = transforms.Compose([
        transforms.Resize(size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.86597056, 0.88463002, 0.87491087],
                             std=[0.20686628, 0.18201602, 0.18485524])
    ])
    return T(image).unsqueeze(0).to(device)

def autoregressive_decode(model, image, prefix, max_decode_len, eos_id, token_whitelist=None, token_blacklist=None):
    model.eval()
    with torch.no_grad():
        memory = model.encode(image)
        context = torch.tensor(prefix, dtype=torch.int32).repeat(image.shape[0], 1).to(device)
        for _ in range(max_decode_len):
            if all(eos_id in k for k in context): break
            mask = subsequent_mask(context.shape[1]).to(device)
            logits = model.decode(memory, context, tgt_mask=mask, tgt_padding_mask=None)
            logits = model.generator(logits)[:, -1, :]
            logits = pred_token_within_range(logits.detach(), white_list=token_whitelist, black_list=token_blacklist)
            _, next_tokens = greedy_sampling(logits)
            context = torch.cat([context, next_tokens], dim=1)
    return context

def rescale_bbox(bbox, src, tgt):
    ratio = [tgt[0] / src[0], tgt[1] / src[1]] * 2
    return [[int(round(i * j)) for i, j in zip(entry, ratio)] for entry in bbox]

def clean_cell_content(text):
    text = text.replace('\n', ' ').replace('\t', ' ').strip()
    text = re.sub(r'(\w)\s*-\s*(\w)', r'\1-\2', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(\d)\.\s+(\d)', r'\1.\2', text)
    text = re.sub(r'\s+([:;,.])', r'\1', text)
    return text

def build_table_with_empty_cells(pred_html, pred_cells, pred_bboxes):
    soup = bs(''.join(pred_html), 'html.parser')
    table = soup.find('table')
    header_row = table.find('tr') if table else None
    header_cols = [th.get_text(strip=True) != '' for th in header_row.find_all(['td', 'th'])] if header_row else []

    rows = defaultdict(list)
    for idx, bbox in enumerate(pred_bboxes):
        y_center = (bbox[1] + bbox[3]) / 2
        for key in rows:
            if abs(key - y_center) < 15:
                rows[key].append((bbox, idx))
                break
        else:
            rows[y_center].append((bbox, idx))

    sorted_rows = sorted(rows.items(), key=lambda x: x[0])
    structured_rows = [sorted(r, key=lambda x: (x[0][0] + x[0][2]) / 2) for _, r in sorted_rows]
    all_x_centers = sorted(((bbox[0] + bbox[2]) / 2) for bbox, _ in sum(structured_rows, []))
    canonical_cols = []
    col_thresh = 30
    for x in all_x_centers:
        if not canonical_cols or abs(x - canonical_cols[-1]) > col_thresh:
            canonical_cols.append(x)
    num_cols = len(canonical_cols)

    html_rows = []
    for row in structured_rows:
        row_cells = [""] * num_cols
        for bbox, idx in row:
            x_center = (bbox[0] + bbox[2]) / 2
            col_idx = min(range(num_cols), key=lambda i: abs(canonical_cols[i] - x_center))
            content = pred_cells[idx] if idx < len(pred_cells) else ""
            row_cells[col_idx] = clean_cell_content(content)
        html_rows.append("  <tr>" + "".join(f"<td>{cell}</td>" for cell in row_cells) + "</tr>")
    return "\n".join(html_rows)

def html_table_template(inner_html: str) -> str:
    return f"""
<html>
  <head>
    <meta charset="utf-8"/>
    <style>
      table, th, td {{
        border: 1px solid black;
        border-collapse: collapse;
        font-size: 10px;
        padding: 4px;
      }}
      table {{
        width: 100%;
      }}
    </style>
  </head>
  <body>
    <table>
{inner_html}
    </table>
  </body>
</html>
""".strip()

# === PROCESS FIRST 100 IMAGES ===
image_paths = sorted(list(input_dir.glob("*.png")) + list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.jpeg")))[:100]

for img_path in image_paths:
    try:
        image = Image.open(img_path).convert("RGB")
        image_size = image.size
        img_name = img_path.stem
        print(f"🧠 Processing {img_path.name}")

        # --- STRUCTURE ---
        vocab, model = load_vocab_and_model(
            vocab_path="../unitable/vocab/vocab_html.json",
            max_seq_len=784,
            model_weights=MODEL_DIR / MODEL_FILE_NAME[0],
        )
        img_tensor = image_to_tensor(image, size=(448, 448))
        pred_html = autoregressive_decode(
            model=model,
            image=img_tensor,
            prefix=[vocab.token_to_id("[html]")],
            max_decode_len=512,
            eos_id=vocab.token_to_id("<eos>"),
            token_whitelist=[vocab.token_to_id(i) for i in VALID_HTML_TOKEN]
        )
        pred_html = vocab.decode(pred_html[0].cpu().numpy(), skip_special_tokens=False)
        pred_html = html_str_to_token_list(pred_html)

        # --- BBOX ---
        vocab, model = load_vocab_and_model(
            vocab_path="../unitable/vocab/vocab_bbox.json",
            max_seq_len=1024,
            model_weights=MODEL_DIR / MODEL_FILE_NAME[1],
        )
        img_tensor = image_to_tensor(image, size=(448, 448))
        pred_bbox = autoregressive_decode(
            model=model,
            image=img_tensor,
            prefix=[vocab.token_to_id("[bbox]")],
            max_decode_len=1024,
            eos_id=vocab.token_to_id("<eos>"),
            token_whitelist=[vocab.token_to_id(i) for i in VALID_BBOX_TOKEN[:449]]
        )
        pred_bbox = vocab.decode(pred_bbox[0].cpu().numpy(), skip_special_tokens=False)
        pred_bbox = bbox_str_to_token_list(pred_bbox)
        pred_bbox = rescale_bbox(pred_bbox, src=(448, 448), tgt=image_size)

        # --- CELL ---
        vocab, model = load_vocab_and_model(
            vocab_path="../unitable/vocab/vocab_cell_6k.json",
            max_seq_len=200,
            model_weights=MODEL_DIR / MODEL_FILE_NAME[2],
        )
        cell_tensors = [image_to_tensor(image.crop(b), size=(112, 448)) for b in pred_bbox]
        cell_tensor = torch.cat(cell_tensors, dim=0)
        pred_cell = autoregressive_decode(
            model=model,
            image=cell_tensor,
            prefix=[vocab.token_to_id("[cell]")],
            max_decode_len=200,
            eos_id=vocab.token_to_id("<eos>"),
            token_blacklist=[vocab.token_to_id(i) for i in INVALID_CELL_TOKEN]
        )
        pred_cell = vocab.decode_batch(pred_cell.detach().cpu().numpy(), skip_special_tokens=False)
        pred_cell = [cell_str_to_token_list(i) for i in pred_cell]
        pred_cell = [re.sub(r'(\d)\.\s+(\d)', r'\1.\2', i) for i in pred_cell]

        # --- BUILD & SAVE HTML ---
        html_code = build_table_with_empty_cells(pred_html, pred_cell, pred_bbox)
        final_html = html_table_template(html_code)
        out_dir = output_base / img_name
        out_dir.mkdir(parents=True, exist_ok=True)
        html_path = out_dir / "generated.html"
        html_path.write_text(bs(final_html).prettify(), encoding="utf-8")
        print(f"✅ Saved to {html_path}")
    except Exception as e:
        print(f"❌ Failed on {img_path.name}: {e}")

