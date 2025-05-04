import os
import django
import time
import cv2
from deepface import DeepFace

# Setup Django environment (change path to your project)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from netflix.models import UserMood  # Replace with your actual app name

def detect_mood():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None

    try:
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        emotion = result[0]['dominant_emotion']
        return emotion
    except Exception as e:
        print("DeepFace Error:", e)
        return None

def update_mood_in_db(user_id=1):
    mood = detect_mood()
    if mood:
        UserMood.objects.update_or_create(user_id=user_id, defaults={'mood': mood})
        print(f"Updated mood to: {mood}")

if __name__ == "__main__":
    while True:
        update_mood_in_db()
        time.sleep(10)
