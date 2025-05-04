from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
import datetime
import cv2  # For image processing
import socket  # To fetch local IP
from main_ai import AI_app
import traceback


app = Flask(__name__)
CORS(app)

# ==================================================================
# Configuration (MODIFY THIS SECTION)
# ==================================================================
# Get your computer's local IP automatically
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# YOUR_LOCAL_IP = get_local_ip()  # Auto-detects IP (e.g., 192.168.1.5)
YOUR_LOCAL_IP = "172.18.41.181" # Auto-detects IP (e.g., 192.168.1.5)
PORT = 8002
# ==================================================================

# Folder paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
RESULTS_FOLDER = os.path.join(BASE_DIR, 'results')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)
fore_ckpt_path='app/ckpts/yolo_sclera.pt'
vein_ckpt_path ='app/ckpts/vein_ckpt.pt'
pipe = AI_app(fore_ckpt_path,vein_ckpt_path,if_cropped=True)

def process_image(input_path, output_folder):
    """Example: Convert to grayscale"""
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError("Could not read image")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Generate unique filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    output_filename = f"result_{timestamp}.jpg"
    output_path = os.path.join(output_folder, output_filename)
    cv2.imwrite(output_path, gray)
    return output_filename

@app.route('/uploads/<filename>')
def serve_uploaded_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/results/<filename>')
def serve_result_image(filename):
    return send_from_directory(RESULTS_FOLDER, filename)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Save uploaded image
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(filename, filepath)
        file.save(filepath)
        
        images = [filepath]
        x = pipe.execute(images)
        print(x)

        # Process image
        result_filename = process_image(filepath, RESULTS_FOLDER)

        # ==================================================================
        # Updated URL generation using your local IP
        # ==================================================================
        # captured_url = f"http://{YOUR_LOCAL_IP}:{PORT}/uploads/{filename}"
        captured_url = f"http://{YOUR_LOCAL_IP}:{PORT}/{x}"

        # result_url = f"http://{YOUR_LOCAL_IP}:{PORT}/results/{result_filename}"
        result_url = f"http://{YOUR_LOCAL_IP}:{PORT}/{x}"

        print(x)
        print(captured_url)
        return jsonify({
            "status": "success",
            "captured_image_url": captured_url,
            "resultant_image_url": result_url
        }), 200

    except Exception as e:
        traceback.print_exc()  # Add this line

        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print(f"Server accessible at: http://{YOUR_LOCAL_IP}:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
