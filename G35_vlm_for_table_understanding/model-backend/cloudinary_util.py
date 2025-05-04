import cloudinary
import cloudinary.uploader
    
cloudinary.config( 
    cloud_name = "divc1cuwa", 
    api_key = API_KEY, 
    api_secret = API_SECRET,
    secure=True
)

def upload_image(image_path):
  upload_result = cloudinary.uploader.upload(image_path)
  return upload_result["secure_url"]
