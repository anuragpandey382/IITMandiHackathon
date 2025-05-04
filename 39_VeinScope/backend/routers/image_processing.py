from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import io
from db.mongo import fs  # GridFS instance
from utils.image_ops import process_image  # your image processing logic

router = APIRouter()



@router.post("/process-images/")
async def process_images(files: list[UploadFile] = File(...)):
    download_urls = []

    for file in files:
        image_bytes = await file.read()
        if not image_bytes:
            continue

        original_id = fs.put(image_bytes, filename=file.filename, metadata={"type": "original"})

        print("Processing....")

        # Updated process_image() returns a list of processed image bytes
        processed_images = process_image(image_bytes)

        for idx, img_bytes in enumerate(processed_images[:-1]):
            filename = f"processed_{idx}_" + file.filename
            processed_id = fs.put(
                img_bytes,
                filename=filename,
                metadata={"type": "processed", "original_id": str(original_id)}
            )

            url = f"https://your-domain/get-image/{str(processed_id)}" # Enter your backend/server
            download_urls.append(url)

        diseases = processed_images[-1]
        for i in diseases:
            if(i == "Diagnosis"):
                continue
            print(i,diseases[i])
            diseases[i] = float(diseases[i])

        print(diseases)

    return {"download_urls": download_urls, "diseases": diseases}



