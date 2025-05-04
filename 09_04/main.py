import os
import fitz
from togetherAI import run

def convert_pdf_to_pngs(pdf_path):
    """Convert each page of PDF to PNG and return the filenames"""
    png_files = []
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            pix = page.get_pixmap()
            output_filename = f"input_page_{i+1}.png"
            pix.save(output_filename)
            png_files.append(output_filename)
        doc.close()
    except Exception as e:
        print(f"Error converting PDF: {e}")
    return png_files

def main(base="input"):
    if os.path.exists(f"{base}.png"):
        opt=run(f"{base}.png")
    elif os.path.exists(f"{base}.jpg"):
        opt=run(f"{base}.jpg")
    
    elif os.path.exists(f"{base}.pdf"):
        png_files = convert_pdf_to_pngs(f"{base}.pdf")
        if not png_files:
            return -1

        opt=0
        for png_file in png_files:
            opt+=run(png_file,opt)
    else:
        return -1      
    return opt

if __name__ == "__main__":
    base = "test_1"
    main(base)
