import easyocr
import os
from PIL import UnidentifiedImageError
import torch
import cv2
import torch
 
# Initialize models
# clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
# clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())

def preprocess_image(image_path):
    try:
        # Load image using OpenCV (better for array processing)
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Resize if too large
        if max(image.shape) > 1000:
            scale = 1000 / max(image.shape)
            image = cv2.resize(image, None, fx=scale, fy=scale)

        # Denoise (optional)
        gray = cv2.fastNlMeansDenoising(gray, h=15)

        # Adaptive thresholding for binarization
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 31, 15
        )

        # Save temp processed file
        temp_path = "temp_processed.png"
        cv2.imwrite(temp_path, thresh)
        return temp_path
    except Exception as e:
        print(f"❌ Preprocessing error: {e}")
        return image_path  # fallback


def extract_text_with_easyocr(image_path):
    try:
        if not os.path.exists(image_path):
            return f"❌ Error: File not found - {image_path}"

        # Apply preprocessing
        preprocessed_path = preprocess_image(image_path)

        # Run OCR
        result = reader.readtext(preprocessed_path, detail=0)
        text = " ".join(result)

        # Cleanup temp image
        if preprocessed_path != image_path:
            os.remove(preprocessed_path)

        return text.strip() if text.strip() else "[No text detected]"

    except UnidentifiedImageError:
        return f"❌ Error: Unsupported or corrupted image file: {image_path}"
    
    except Exception as e:
        return f"❌ Error processing image: {str(e)}"


def process_image(image_path):
    ocr_result = extract_text_with_easyocr(image_path)
    return ocr_result


# from transformers import AutoTokenizer, AutoModelForCausalLM
# model_name = "mistralai/Mistral-7B-Instruct-v0.2"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16) 
# def generate_explanation(ocr_result):
#     prompt = f"""
#         You are an assistant that explains MATLAB error messages or log content.
#         Given this raw text (from an OCR engine), explain in 4-5 sentences what the text most likely refers to.
#         Text:
#         \"\"\"{ocr_result}\"\"\"

#         Explanation:
#     """
#     inputs = tokenizer(prompt, return_tensors="pt")  # Don't use .to("cuda")
#     outputs = model.generate(**inputs, max_new_tokens=150, do_sample=True, temperature=0.7)
#     return tokenizer.decode(outputs[0], skip_special_tokens=True).split("Explanation:")[-1].strip()


def imgFormat(imgfile):
    ocr = process_image(imgfile)
    # exp = generate_explanation(ocr)
    return ocr
    

if __name__ == "__main__":
    image_path = "images/2.png"
    ocr = process_image(image_path)
    # exp = generate_explanation(ocr)
    print("OCR Result:", ocr)
    # print("Explanation:", exp)
    