from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import cv2
import numpy as np
import os
import uuid
import torch
from PIL import Image
import io
import matplotlib.pyplot as plt
import pandas as pd
from tempfile import NamedTemporaryFile, mkdtemp
import shutil
from typing import Optional, List, Dict, Any
import logging
import time
from Tongue_crack_detection_model import detect_tongue_cracks_advanced
# Import the TonguePapillaeAnalyzer class
from jaggedScore import jagged_tongue
from tongue_papillae_analyzer import TonguePapillaeAnalyzer
from llmcall import generate_summary
import requests
from fastapi import FastAPI, Request, HTTPException

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tongue-analysis-api")

# Check if CUDA is available for PyTorch
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {DEVICE}")

# Constants
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global variables for models
sam_model = None
sam_predictor = None
roboflow_client = None

# Model loading functions
def load_sam_model(checkpoint_path="sam_vit_h.pth", model_type="vit_h"):
    """Load the Segment Anything Model"""
    try:
        from segment_anything import sam_model_registry, SamPredictor
        
        logger.info(f"Loading SAM model from {checkpoint_path}")
        sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
        sam.to(DEVICE)
        predictor = SamPredictor(sam)
        
        logger.info("SAM model loaded successfully")
        return sam, predictor
    except Exception as e:
        logger.error(f"Failed to load SAM model: {str(e)}")
        return None, None

def load_roboflow_client(api_key="UySFJBcSCBCxmwiEA9ea"):
    """Load the Roboflow client for tongue detection"""
    try:
        from inference_sdk import InferenceHTTPClient
        
        logger.info("Initializing Roboflow client")
        client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key=api_key
        )
        
        logger.info("Roboflow client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Roboflow client: {str(e)}")
        return None

@app.on_event("startup")
async def startup_event():
    """Initialize models when the server starts"""
    global sam_model, sam_predictor, roboflow_client
    
    # Load SAM model
    sam_model, sam_predictor = load_sam_model()
    
    # Load Roboflow client
    roboflow_client = load_roboflow_client()
    
    # Initialize papillae analyzer
    logger.info("Server startup complete")

def save_uploaded_file(file: UploadFile) -> str:
    """Save the uploaded file and return the file path"""
    try:
        temp_file = os.path.join(OUTPUT_DIR, f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}")
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return temp_file
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

def read_image_file(file: UploadFile) -> np.ndarray:
    """Read image file into OpenCV format"""
    try:
        contents = file.file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        file.file.seek(0)  # Reset file pointer for potential reuse
        return img
    except Exception as e:
        logger.error(f"Error reading image: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

def detect_tongue_roboflow(image: np.ndarray):
    """Detect tongue in the image using Roboflow"""
    if roboflow_client is None:
        raise HTTPException(status_code=500, detail="Roboflow client not initialized")
    
    try:
        result = roboflow_client.infer(image, model_id="tongue-93kco/3")
        
        if "predictions" in result and len(result["predictions"]) > 0:
            prediction = result["predictions"][0]
            x = prediction["x"]
            y = prediction["y"]
            logger.info(f"Detected tongue at: x={x}, y={y}")
            return np.array([[x, y]])
        else:
            logger.warning("No tongue detected by Roboflow")
            # Fallback to center of the image
            height, width = image.shape[:2]
            return np.array([[width/2, height/2]])
    except Exception as e:
        logger.error(f"Error in Roboflow detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Roboflow detection failed: {str(e)}")

def segment_tongue_sam(image: np.ndarray, input_point: np.ndarray):
    """Segment the tongue using Segment Anything Model"""
    if sam_predictor is None:
        raise HTTPException(status_code=500, detail="SAM model not initialized")
    
    try:
        # Convert to RGB for SAM
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Set image in predictor
        sam_predictor.set_image(image_rgb)
        
        # Predict mask
        input_label = np.array([1])  # Positive label for tongue point
        masks, _, _ = sam_predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=False,
        )
        
        # Get the mask
        mask = masks[0]
        
        # Create segmented image
        segmented_image = np.zeros_like(image)
        segmented_image[mask] = image[mask]
        
        logger.info("Tongue segmentation completed")
        return segmented_image, mask
    except Exception as e:
        logger.error(f"Error in SAM segmentation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SAM segmentation failed: {str(e)}")

def detect_white_coating(image: np.ndarray, mask: np.ndarray) -> Dict[str, Any]:
    """Detect white coating on the tongue"""
    try:
        # Ensure mask is in uint8 format
        mask = mask.astype(np.uint8) * 255  # Convert bool mask to uint8 (0 or 255)
        
        # Apply mask to focus only on the tongue area
        masked_image = cv2.bitwise_and(image, image, mask=mask)
        
        # Convert to HSV color space
        hsv = cv2.cvtColor(masked_image, cv2.COLOR_BGR2HSV)
        
        # Define white color range in HSV
        lower_white = np.array([0, 0, 180])
        upper_white = np.array([180, 80, 255])
        
        # Create a mask for white regions
        white_mask = cv2.inRange(hsv, lower_white, upper_white)
        
        # Find contours of white areas
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw contours
        coating_visualization = image.copy()
        cv2.drawContours(coating_visualization, contours, -1, (0, 255, 0), 2)
        
        # Calculate white coating percentage
        white_pixels = cv2.countNonZero(white_mask)
        tongue_pixels = cv2.countNonZero(mask)
        if tongue_pixels > 0:
            white_percent = (white_pixels / tongue_pixels) * 100
        else:
            white_percent = 0
            
        logger.info(f"White coating detection completed: {white_percent:.2f}%")
        
        # Save visualization
        coating_viz_path = os.path.join(OUTPUT_DIR, f"coating_{uuid.uuid4()}.jpg")
        cv2.imwrite(coating_viz_path, coating_visualization)
        
        return {
            "white_coating_percentage": white_percent,
            "visualization_path": coating_viz_path
        }
    except Exception as e:
        logger.error(f"Error in white coating detection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"White coating detection failed: {str(e)}")

def analyze_papillae(image_path: str) -> Dict[str, Any]:
    """Analyze papillae in the tongue image"""
    try:
        # Create analyzer instance
        analyzer = TonguePapillaeAnalyzer(
            patch_size=64, 
            threshold_adjust=1.2,
            min_papillae_size=15,
            max_papillae_size=400
        )
        
        # Analyze image
        results_df, visualization_image, segmentation_viz, patch_viz = analyzer.analyze_image(image_path)
        
        # Generate report
        report = analyzer.generate_report(results_df)
        
        # Create visualizations
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        visualization = analyzer.visualize_results(image, results_df)
        
        # Save visualizations
        viz_path = os.path.join(OUTPUT_DIR, f"papillae_{uuid.uuid4()}.jpg")
        plt.figure(figsize=(18, 12))
        
        plt.subplot(2, 2, 1)
        plt.title("Original Image")
        plt.imshow(image)
        plt.axis('off')
        
        plt.subplot(2, 2, 2)
        plt.title("Tongue Segmentation")
        plt.imshow(segmentation_viz)
        plt.axis('off')
        
        plt.subplot(2, 2, 3)
        plt.title("Detected Papillae")
        plt.imshow(visualization)
        plt.axis('off')
        
        plt.subplot(2, 2, 4)
        plt.title("Papillae Size vs Redness")
        if len(results_df) > 0:
            plt.scatter(
                results_df['size'], 
                results_df['redness_score'], 
                c=results_df['redness_score'], 
                cmap='coolwarm',
                alpha=0.7
            )
            plt.colorbar(label='Redness Score')
            plt.xlabel('Papilla Size (pixels)')
            plt.ylabel('Redness Score')
        else:
            plt.text(0.5, 0.5, "No papillae detected", ha='center', va='center')
            
        plt.tight_layout()
        plt.savefig(viz_path)
        plt.close()
        
        # Save CSV if data exists
        csv_path = None
        if len(results_df) > 0:
            csv_path = os.path.join(OUTPUT_DIR, f"papillae_{uuid.uuid4()}.csv")
            results_df.to_csv(csv_path, index=False)
        
        logger.info("Papillae analysis completed")
        
        return {
            "total_papillae": report['total_papillae'],
            "avg_size": float(report['avg_size']),
            "avg_redness": float(report['avg_redness']),
        }
    except Exception as e:
        logger.error(f"Error in papillae analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Papillae analysis failed: {str(e)}")
    
API_KEY = "AIzaSyBWb5O_8-tYNazvqOAjBWdcqmU--JF-EAg"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

@app.post("/chat")
async def chat(request: Request):
    """Handle chat messages"""
    try:
        data = await request.json()
        user_message = data.get("message", "").strip()
        if not user_message:
            raise HTTPException(status_code=400, detail="Please enter a message.")

        logger.info(f"Received message: {user_message[:30]}...")

        payload = {
            "contents": [{
                "parts": [{"text": user_message}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }

        headers = {"Content-Type": "application/json"}

        # Call Gemini API
        response = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()

        try:
            reply = response_data["candidates"][0]["content"]["parts"][0]["text"]
            logger.info(f"Generated response: {reply[:30]}...")
            return {"reply": reply}
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing API response: {e}")
            logger.error(f"Response data: {response_data}")
            raise HTTPException(status_code=500, detail="Error parsing API response")

    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        raise HTTPException(status_code=502, detail=f"API Error: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    

@app.post("/analyze_tongue", response_class=JSONResponse)
async def analyze_tongue(file: UploadFile = File(...)):
    """
    Analyze a tongue image for segmentation, white coating, and papillae detection
    """
    start_time = time.time()
    logger.info(f"Received request to analyze tongue image: {file.filename}")
    
    try:
        # Save uploaded file
        file_path = save_uploaded_file(file)
        logger.info(f"Saved file to {file_path}")
        
        # Read image
        image = cv2.imread(file_path)
        if image is None:
            raise HTTPException(status_code=400, detail="Could not read image file")
        
        # Step 1: Detect tongue point using Roboflow
        input_point = detect_tongue_roboflow(image)
        
        # Step 2: Segment tongue using SAM
        segmented_image, mask = segment_tongue_sam(image, input_point)
        
        # Save segmented image
        segmented_path = os.path.join(OUTPUT_DIR, f"segmented_{uuid.uuid4()}.jpg")
        cv2.imwrite(segmented_path, segmented_image)
        
        # Step 3: Detect white coating
        coating_results = detect_white_coating(segmented_image, mask)
        
        # Step 4: Analyze papillae (using the original saved file)
        papillae_results = analyze_papillae(segmented_path)
        redness = papillae_results["avg_redness"]*10
        result_cracked = detect_tongue_cracks_advanced(segmented_path)
        morphed = os.path.join(OUTPUT_DIR, f"coating_{uuid.uuid4()}.jpg")
        cv2.imwrite(morphed, result_cracked["overlay"])
        score_cracked = {"morph": morphed, "score": result_cracked["score"]}
        # Prepare response
        # score_cracked = {result_cracked["score"]
        response = {
            "Jaggedness" : "25",
            "Cracks" : score_cracked,
            "redness" : redness,
            "segmented_image_path": segmented_path,
            "white_coating": coating_results,
            "papillae_analysis": papillae_results
        }
        summary = generate_summary(response)
        Nutrition_Score = round(( (10 - coating_results["white_coating_percentage"]/7) * 0.4 + papillae_results["avg_size"] * 0.3 +  papillae_results["avg_redness"]* 0.3 ), 2)
        Mantle_Score = (10 - score_cracked["score"]/10)*0.5 + (10-5)*0.5     
        # Mantle_Score = 45
        jagged_Score = jagged_tongue(segmented_path)
        response = {
            "Jaggedness" : jagged_Score["score"]*10,
            "Summary" : summary["reply"],
            "Cracks" : score_cracked,
            "NutritionScore" : Nutrition_Score*10,
            "MantleScore" : Mantle_Score*10,
            "redness" : redness,
            "segmented_image_path": segmented_path,
            "white_coating": coating_results,
            "papillae_analysis": papillae_results
        }
        logger.info(f"Analysis completed seconds")
        print(response)
        return JSONResponse(content=response)
    
    except HTTPException as http_exc:
        logger.error(f"HTTP exception: {http_exc.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/image/{image_path:path}")
async def get_image(image_path: str):
    """Retrieve an image from the output directory"""
    full_path = os.path.join(OUTPUT_DIR, os.path.basename(image_path))
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(full_path)

@app.get("/csv/{csv_path:path}")
async def get_csv(csv_path: str):
    """Retrieve a CSV file from the output directory"""
    full_path = os.path.join(OUTPUT_DIR, os.path.basename(csv_path))
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="CSV file not found")
    return FileResponse(full_path)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "sam_model": "loaded" if sam_model is not None else "not loaded",
        "roboflow_client": "loaded" if roboflow_client is not None else "not loaded",
    }
    return JSONResponse(content=health_status)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)