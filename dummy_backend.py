from flask import Flask, request, jsonify
import random
import time
import os

# Initialize Flask app
app = Flask(__name__)

# Optional: Define an upload folder if you WANTED to save the file temporarily
# UPLOAD_FOLDER = 'backend_uploads/'
# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/predict', methods=['POST'])
def predict():
    """
    Dummy endpoint to simulate fake speech detection.
    Accepts an audio file but randomly returns REAL/FAKE.
    """
    print("Received request at /predict") # Log to console

    # --- Basic Input Validation ---
    if 'inputFile' not in request.files:
        print("Error: No 'inputFile' part in the request")
        return jsonify({'error': 'No audio file part found in the request.'}), 400

    file = request.files['inputFile']

    # Check if the user submitted an empty part without filename
    if file.filename == '':
        print("Error: No selected file")
        return jsonify({'error': 'No selected audio file.'}), 400

    # --- Simulate Model Processing ---
    try:
        # We don't actually need to save or process the file for this dummy version
        print(f"Received file: {file.filename} (Type: {file.content_type})")
        # file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        # file.save(file_path) # Uncomment if you want to save the file

        # Simulate processing time
        processing_delay = random.uniform(0.1, 1.5) # Simulate 0.1 to 1.5 seconds
        print(f"Simulating processing for {processing_delay:.2f} seconds...")
        time.sleep(processing_delay)

        # --- Generate Dummy Prediction ---
        possible_predictions = ['REAL', 'FAKE']
        prediction_result = random.choice(possible_predictions)
        # Generate a plausible confidence score
        confidence_score = random.uniform(0.65, 0.99) if prediction_result != "ERROR" else 0.0

        print(f"Dummy Prediction: {prediction_result}, Confidence: {confidence_score:.2f}")

        # --- Prepare JSON Response (Matching Streamlit Expectations) ---
        response_data = {
            'prediction': prediction_result,
            'confidence': confidence_score,
            'model_processing_time_ms': int(processing_delay * 1000), # Optional: Include dummy time
            'error': None # Indicate success from backend's perspective
        }

        # Optional: Clean up saved file if you saved it
        # if os.path.exists(file_path):
        #     os.remove(file_path)

        return jsonify(response_data), 200 # Return JSON with 200 OK

    except Exception as e:
        # Catch any unexpected errors during dummy processing
        print(f"An unexpected error occurred: {e}")
        return jsonify({'error': f'An internal server error occurred: {str(e)}'}), 500


# --- Run the Flask App ---
if __name__ == '__main__':
    # Make accessible on your network, change port if 5000 is busy
    # Set debug=False for any "production" use (even for hackathon demo)
    app.run(host='0.0.0.0', port=5000, debug=True)