# Dl_hackathon
# Eye Vessel Segmentation and Health Indicator Web Application

## Overview

This web application processes images of the eye to segment the retinal vessels and provides a potential health indicator based on the vessel structure. It uses a deep learning model (U-Net with ResNet34 backbone) trained for vessel segmentation, followed by feature extraction from the segmented vessels and clustering using a pre-trained KMeans model.

## IMPORTANT
We have not included the models in the repo. The user is requested to follow following steps:

1. Include the dataset on same level as test_images [sqb
2. Open unet_feat -> unet_training_independent.py 
3. Recheck the BASE_PATH variable and to train model faster switch from (1024, 1024) to    (512, 512) or (256, 256), but not to increase batch_size more than 4
4. 3 Models will be saved in models files after successful execution [.pth, .jolib] in the models folder and predicted images in predictions folder
5. To get the independet code for unet training -> unet_feat_combined.py
6. To get the independet code for feature extraction -> feature_extractor_independent.py
7. Now, we can move towards the web folder.

The application performs the following steps:

1.  **Image Upload:** Accepts an image file through a web interface or an API endpoint.
2.  **Region of Interest (ROI) Detection (Optional):** Attempts to detect the eye region in the uploaded image using a Haar Cascade classifier. If an eye is detected, the segmentation is focused on this ROI.
3.  **Vessel Segmentation:** Uses a pre-trained fastai U-Net model to segment the retinal vessels in the input image (or the detected ROI).
4.  **Post-processing:** Applies morphological operations (connected components analysis and closing) to refine the segmentation mask.
5.  **Feature Extraction:** Extracts quantitative features from the segmented binary mask, such as density, branch points, endpoints, tortuosity, vein length, and vein width.
6.  **Feature Normalization:** Normalizes the extracted features using a pre-trained MinMaxScaler.
7.  **Health Indicator Prediction:** Uses a pre-trained KMeans clustering model to classify the normalized features into predefined health-related clusters.
8.  **Output:** Returns the segmented vessel mask as a Base64 encoded PNG image and the predicted health indicator text as a JSON response.

## Prerequisites

Before running the application, ensure you have the following installed:

* **Git** (for cloning the repository)
* **Python 3.x**
* **pip** (Python package installer)
* **Required Python libraries:** You can install them using the `requirements.txt` file (create one with the following content):

    ```
    check requirements.txt
    ```
* **Pre-trained models and other necessary files:**
    * `bestmodel.pth`: The weights file for the vessel segmentation U-Net model.
    * `scaler.joblib`: The pre-trained MinMaxScaler model for feature normalization.
    * `kmeans.joblib`: The pre-trained KMeans clustering model.
    * `haarcascade_eye.xml`: The Haar Cascade XML file for eye detection.

## Setup
 (`index.html`) is expected to be in the `templates` directory.

## Running the Application

1.  **Install the required Python libraries:** 

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Flask development server:** In the same `dl/dlhackathon` directory, execute:

    ```bash
    python app.py
    ```
    
    or
    ```
    python3 app.py
    ```

3.  The server will start, and you should see output similar to:

    ```
    Starting Flask server on port 5001...
     * Serving Flask app 'app'
     * Debug mode: on
    ...
    ```
    **IMP**
    check on the link it gives of for 127.** 
    If you got error saying 5001 port is already used, either kill that process or visit app.py and index.html in templates folder and change 5001 to 5002.

4.  **Open the website:** Open your web browser and go to `http://127.0.0.1:5002/` (or the address and port shown in your terminal). You should see the web interface provided by `templates/index.html`.

5.  **Upload an image:** Use the file input field to select an eye image and click "Analyze". The results (health indicator and segmented vessel image) will be displayed on the page.


