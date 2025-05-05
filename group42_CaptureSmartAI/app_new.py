from flask import Flask, render_template, Response
import torch
import torchvision.transforms as transforms
from PIL import Image
import cv2
import timm
from torch import nn
import numpy as np

app = Flask(__name__)

# 1. Updated Model Definition
class EfficientNetRegressionModel(nn.Module):
    def __init__(self):
        super().__init__()

        # EfficientNet-Lite0 as feature extractor
        self.feature_extractor = timm.create_model('efficientnet_lite0', pretrained=True, num_classes=0)

        # Output is already [B, 1280]
        self.layer_norm = nn.LayerNorm(1280)

        self.fnn = nn.Sequential(
            nn.Linear(1280, 128),
            nn.ReLU()
        )

        self.head_ss_var  = nn.Linear(128, 1)
        self.head_iso_var = nn.Linear(128, 1)

    def forward(self, x):
        # Feature extraction
        x = self.feature_extractor(x)  # [B, 1280]

        # Layer normalization
        x = self.layer_norm(x)

        # Fully connected layers
        x = self.fnn(x)

        # Separate heads for SS and ISO predictions
        ss_var = self.head_ss_var(x)
        iso_var = self.head_iso_var(x)

        return ss_var, iso_var

# 2. Preprocessing
def preprocess_frame(frame_bgr):
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb).resize((224, 224))
    gray = img.convert("L")
    img = Image.merge("RGB", (gray, gray, gray))
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5]*3, std=[0.5]*3)
    ])
    return transform(img).unsqueeze(0)

# Initialize model
model = EfficientNetRegressionModel()
state = torch.load("best_model_ss.pth", map_location=torch.device("cpu"))
model.load_state_dict(state)
model.eval()

# 3. Video Generator with Motion Detection
def generate_frames():
    cap = cv2.VideoCapture(0)  # OpenCV captures video from the default webcam
    previous_frame = None
    last_ss_prediction, last_iso_prediction = None, None  # Store last predictions

    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # Convert current frame to grayscale for motion detection
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

            # Motion Detection: Compare with the previous frame
            if previous_frame is None:
                previous_frame = gray_frame
                continue

            frame_diff = cv2.absdiff(previous_frame, gray_frame)
            _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
            motion_detected = np.sum(thresh) > 5000  # Motion threshold

            if motion_detected:
                inp = preprocess_frame(frame)
                with torch.no_grad():
                    ss_var, iso_var = model(inp)

                # Update predictions
                last_ss_prediction = ss_var.item()
                last_iso_prediction = iso_var.item()

            # Overlay predictions on the frame (use last predictions)
            display = frame.copy()
            if last_ss_prediction is not None and last_iso_prediction is not None:
                text = f"SS Prediction: {last_ss_prediction:+.3f}   ISO Prediction: {last_iso_prediction:+.3f}"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.7  # Reduced font scale
                font_thickness = 1  # Reduced font thickness
                text_color = (0, 102, 255)  # Subtle blue color
                shadow_color = (0, 0, 0)  # Black shadow for contrast

                # Draw shadow for better visibility
                cv2.putText(display, text, (10, 30), font, font_scale, shadow_color, font_thickness + 1)
                # Draw main text
                cv2.putText(display, text, (10, 30), font, font_scale, text_color, font_thickness)

            # Update the previous frame
            previous_frame = gray_frame

            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', display)
            frame = buffer.tobytes()

            # Yield the frame to be displayed
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# 4. Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)