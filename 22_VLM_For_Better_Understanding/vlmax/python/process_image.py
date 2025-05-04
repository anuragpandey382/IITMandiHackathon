import sys
import json
import os
from PIL import Image
import pytesseract

def process_image(image_path):
    """Process an image with OCR and return the results."""
    try:
        # Validate image format
        img_type = image_path.split('.')[-1].lower()
        if img_type not in ['jpeg', 'png', 'jpg']:
            return {
                "success": False,
                "error": f"Unsupported image format: {img_type}"
            }
            
        # Open the image and run OCR
        with Image.open(image_path) as img:
            # For images with transparency, convert to RGB to avoid OCR issues
            if img.mode == 'RGBA':
                img = img.convert('RGB')
                
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        parsed_words = []
        for i, word in enumerate(ocr_data['text']):
            # Only include non-empty words with positive confidence
            if word.strip() and int(ocr_data['conf'][i]) > 0:
                x, y = ocr_data['left'][i], ocr_data['top'][i]
                w, h = ocr_data['width'][i], ocr_data['height'][i]
                parsed_words.append({
                    "word": word,
                    "confidence": int(ocr_data['conf'][i]),
                    "bbox": [x, y, x + w, y + h]
                })

        # Return OCR results
        return {
            "success": True,
            "ocr_data": parsed_words,
            "word_count": len(parsed_words),
            "image_dimensions": img.size
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    image_path = ""
    
    try:
        # Check if an image path is provided
        if len(sys.argv) < 2:
            print(json.dumps({"success": False, "error": "No image path provided"}))
            sys.exit(1)

        image_path = sys.argv[1]
        
        # Validate if file exists
        if not os.path.exists(image_path):
            print(json.dumps({"success": False, "error": "Image file not found"}))
            sys.exit(1)

        # Process the image
        result = process_image(image_path)
        
        # Print OCR results as JSON
        print(json.dumps(result))
        
    except Exception as e:
        # Handle any unexpected exceptions
        print(json.dumps({"success": False, "error": f"Unexpected error: {str(e)}"}))
    
    finally:
        # Always delete the image file, regardless of success or failure
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                # If we can't delete the file, add this information to output
                print(json.dumps({"success": False, "error": f"Failed to delete image file: {str(e)}"}), file=sys.stderr)