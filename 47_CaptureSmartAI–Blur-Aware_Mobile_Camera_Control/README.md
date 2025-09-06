# Capture Smart AI-Blur Aware Mobile Camera Control

## 📱 Project Overview

**Aim:**  
To reduce motion blur in captured images by dynamically adjusting camera parameters such as **shutter speed** and **ISO** based on real-time analysis of **motion**, **brightness**, and **blur**. The app provides two camera modes:
- **AI Camera**: Analyzes each frame using OpenCV and adjusts parameters automatically.
- **Normal Camera**: Captures images using the default camera settings.

---

## 🚀 Features

- 📷 **AI-Powered Camera**: Real-time analysis of motion, brightness, and blur using OpenCV.
- 🔧 **Dynamic Shutter Speed and ISO**: Adjusts exposure based on motion/lighting conditions.
- 🔄 **Camera Switch**: Toggle between front and rear cameras.
- 🖼️ **Overlay UI**: Displays motion %, brightness, blur score, shutter speed, and ISO.
- 💡 **Info Toggle**: Show/hide analysis info with a button.
- 🧠 **OpenCV Integration**: Used for image processing and frame analysis.
- 🧪 **Post-Capture Analysis (Python)**: Visualizes blur heatmaps using edge detection and heatmap overlay.

---

## 🧭 Navigation Flow

1. **SplashActivity**  
   - Shows animated splash screen.
   - Navigates to the main menu after a short delay.

2. **MenuActivity**  
   - Offers two options:  
     - 📱 AI Camera (launches `CameraActivity`)  
     - 📷 Normal Camera (launches `NormalCameraActivity`)

3. **CameraActivity (AI Camera)**  
   - Uses `Camera2 API` and `OpenCV` to analyze each frame.
   - Dynamically computes and sets shutter speed and ISO.
   - Captures and saves high-quality deblurred images.

4. **NormalCameraActivity**  
   - Basic camera capture without motion or blur handling.
   - Switch between front and back cameras.
   - Saves standard JPEG images.

---

## 🧪 Post-Capture Image Analysis (Python Tool)

The Python script `test.py` is designed to analyze images captured by the Android app and **visualize the blur levels** using edge detection and heatmap overlays.

### 🔍 What It Does

This script helps you understand how much of the image is sharp versus blurry by processing it through several image-processing stages. Here's a breakdown of the workflow:

1. **Read the Input Image**  
   - The image is loaded using OpenCV.
   - If the image path is invalid or unreadable, it prints an error and exits.

2. **Convert to Grayscale**  
   - The image is converted to grayscale to simplify edge detection since edges are typically detected from intensity changes.

3. **Apply Canny Edge Detection**  
   - Detects edges in the grayscale image using two threshold values (`low_thresh=50`, `high_thresh=150`).
   - This generates a binary map showing where sharp edges exist.

4. **Create a Blur Map**  
   - The edge map is **inverted** using bitwise NOT operation.
   - Areas without edges (low contrast/blurred zones) become bright in the blur map.

5. **Smooth the Blur Map**  
   - Gaussian Blur is applied to make the visualization softer and more continuous.
   - This helps avoid harsh transitions and makes the heatmap more informative.

6. **Generate Heatmap**  
   - A **color heatmap** (using `COLORMAP_JET`) is applied to the smooth blur map.
   - **Red/blue regions** indicate areas of high blur.
   - **Yellow/green regions** indicate sharper zones with strong edge presence.

7. **Display Results**  
   - Uses `matplotlib` to display:
     - Original image (RGB)
     - Edge map from Canny
     - Heatmap showing blur distribution
   - Optionally saves the output if `save_path` is provided.

### 📈 Sample Use Case

```python
image_file = 'bottle_without.jpg'
output_file = 'heatmap_bottle_without.png'
blur_highlight_with_edges(image_file, save_path=output_file)
```

### 🔧 Dependencies

Make sure you have the following installed:

```bash
pip install opencv-python matplotlib numpy
```

### 📌 Notes
- This script is useful for **validating** how well the Android camera app is reducing motion blur.
- Works best on JPEG images captured by either `CameraActivity` or `NormalCameraActivity`.
- The application is named as "Hackethon", you can directly open this folder in Android Studio.

---

## 🛠️ Tech Stack

- **Language**: Java (Android), Python (Post-processing)
- **Framework**: Android SDK
- **Image Processing**: OpenCV (Android + Python)
- **Camera API**: Android Camera2 API
- **UI Design**: XML Layouts
- **Visualization**: Matplotlib (Python)

---

## 🔧 Permissions Used

- `CAMERA`
- `WRITE_EXTERNAL_STORAGE` *(for Android <= API 28)*
- `READ_MEDIA_IMAGES` *(for Android >= API 33)*

Defined in `AndroidManifest.xml`.

---

## 📂 Key Files

| File                    | Purpose                                          |
|-------------------------|--------------------------------------------------|
| `CameraActivity.java`   | Main AI camera logic with adaptive exposure      |
| `NormalCameraActivity.java` | Standard camera logic (default Android camera) |
| `MenuActivity.java`     | Entry point after splash; offers camera options  |
| `SplashActivity.java`   | Animated splash screen logic                     |
| `test.py`               | Python script to generate heatmaps from captured images |
| `AndroidManifest.xml`   | Declares app structure and permissions           |

---

## ✅ How to Run

### Android App:
1. Clone this repository.
2. Open **Hackethon** directory in **Android Studio**.
3. Connect a physical Android device or use an emulator with camera support enabled with USB Debugging.
4. Click **Run** ▶️.
5. The Application should successfully install with name as **Hackethon** 

### Python Script:
1. Install dependencies:
   ```bash
   pip install opencv-python matplotlib numpy
   ```
2. Place captured images in the same folder as `test.py`.
3. Update the `image_file` path in the script and run:
   ```bash
   python test.py
   ```
   This will generate a heatmap of the blurred images.

---

\---

## 🔗 Related Links

- 📹 [Demo Video](https://drive.google.com/file/d/1G_zM2yH7P6x8jg_o3eoyYWtuTgnO0eT2/view?usp=drivesdk)  

---


## 📃 License

This project is for educational and research purposes.
