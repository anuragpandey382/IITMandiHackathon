from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from db.mongo import fs, db
from bson import ObjectId

router = APIRouter()

@router.get("/email-images/{email}")
def get_user_images(email: str):
    cursor = db.fs.files.find({"metadata.uploaded_by": email})
    image_list = []
    for doc in cursor:
        image_list.append({"filename": doc["filename"], "file_id": str(doc["_id"]), "type": doc["metadata"].get("type", "unknown")})
    return {"images": image_list}


@router.get("/get-image/{file_id}")
def get_image(file_id: str):
    try:
        file = fs.get(ObjectId(file_id))
        return StreamingResponse(file, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Image not found: {e}")
