#!/usr/bi/env python3

import argparse
import subprocess
import os
import shutil
from pathlib import Path

def run_pdf2imgcrop(input_path):
    print("📄 Running pdf2cropimg.py...")
    subprocess.run([os.path.join("venv", "bin", "python3"), "pdf2cropimg_infer.py", "--pdf", str(input_path)], check=True)
    print("✅ Finished pdf2imgcrop.py")

def run_unittable():
    print("🤖 Running unittable_final_1.py...")
    subprocess.run(["conda", "run", "-n", "fresh3", "python3", "unitable_infer.py"], check=True)
    print("✅ Finished unittable.py")

def run_htmltocsv():
    print("📊 Running htmltocsv_copy.py...")
    subprocess.run([os.path.join("streamlitenv", "bin", "python3"), "htmltocsv_infer.py"], check=True)
    print("✅ Finished htmltocsv.py")

def copy_outputs(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for folder_name in ["csv_final", "html_final"]:
        src = Path(folder_name)
        dest = output_dir / folder_name
        dest.mkdir(parents=True, exist_ok=True)
        for file in src.glob("*"):
            shutil.copy(file, dest)
        print(f"📁 Copied {folder_name} to {dest}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run full inference pipeline on any document.")
    parser.add_argument("input", type=str, help="Input file path (PDF, image, DOCX, etc.)")
    parser.add_argument("--out", type=str, default="output", help="Directory to store final HTML and CSV outputs")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"❌ Input not found: {input_path}")
        exit(1)

    try:
        run_pdf2imgcrop(input_path)
        run_unittable()
        run_htmltocsv()
        copy_outputs(args.out)
        print(f"\n✅ All done! Output saved to: {args.out}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Pipeline failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
