# import os

# class Config:
#     # Base directory
#     BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
#     # Upload settings
#     UPLOAD_FOLDER = os.path.join(BASE_DIR, '../uploads')
#     ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
#     MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit
    
#     # Security (optional)
#     SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')


import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}