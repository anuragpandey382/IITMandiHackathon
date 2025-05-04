# Tongue Analysis API

## Overview

The Tongue Analysis API provides advanced tongue health analysis capabilities through computer vision and machine learning. This FastAPI-based service detects and analyzes various tongue characteristics including:

- Tongue segmentation
- White coating detection
- Papillae analysis
- Crack detection
- Jaggedness measurement
- Comprehensive health scoring

The system leverages state-of-the-art AI models including Segment Anything Model (SAM) and custom detection algorithms to provide quantitative metrics for tongue diagnosis.

🔗 **Access the app here:** [HealthLingua Analyzer](https://github.com/shubhxtech/Analyzer)

## Features

- **Tongue Segmentation**: Accurately isolates the tongue area from images using the Segment Anything Model (SAM)
- **White Coating Analysis**: Detects and quantifies white coating percentage on the tongue surface
- **Papillae Detection**: Identifies, counts, and analyzes tongue papillae characteristics
- **Crack Detection**: Advanced detection and scoring of tongue cracks
- **Jaggedness Analysis**: Measures tongue edge irregularities
- **Health Scoring**: Provides nutrition and mantle health scores based on tongue characteristics
- **Summary Generation**: AI-generated summary of tongue health findings using Gemini API
- **Chat Interface**: Interactive chat functionality for discussing health concerns

## Installation

### Prerequisites

- Python 3.8 or higher
- CUDA-capable GPU (recommended for optimal performance)
- SAM model checkpoint (`sam_vit_h.pth`)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/shubhxtech/HealthLingue.git
   cd HealthLingue
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download the SAM model checkpoint:
   ```bash
   # Download from https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
   # Rename to sam_vit_h.pth and place in the project root directory
   ```

4. Create output directory:
   ```bash
   mkdir -p output
   ```

## Running the API Server

Start the API server using Uvicorn:

```bash
uvicorn FastApiServer:app --host 0.0.0.0 --port 8000
```

The API will be accessible at `http://localhost:8000`.

## API Endpoints

### `/analyze_tongue` (POST)

Analyzes an uploaded tongue image and returns comprehensive metrics.

**Request**:
- `file`: Image file of the tongue

**Response**:
```json
{
  "Jaggedness": 25.0,
  "Summary": "AI-generated summary of tongue health",
  "Cracks": {
    "morph": "path/to/visualization",
    "score": 3.5
  },
  "NutritionScore": 75.5,
  "MantleScore": 82.5,
  "redness": 6.8,
  "segmented_image_path": "path/to/segmented_image",
  "white_coating": {
    "white_coating_percentage": 15.3,
    "visualization_path": "path/to/visualization"
  },
  "papillae_analysis": {
    "total_papillae": 127,
    "avg_size": 32.5,
    "avg_redness": 0.68
  }
}
```

### `/chat` (POST)

Allows users to ask health-related questions.

**Request**:
```json
{
  "message": "What does high tongue coating indicate?"
}
```

**Response**:
```json
{
  "reply": "AI-generated response about tongue coating"
}
```

### `/health` (GET)

Returns the health status of the API and its components.

### `/image/{image_path}` (GET)

Retrieves generated visualization images.

### `/csv/{csv_path}` (GET)

Retrieves generated CSV data files.

## Project Structure

- `FastApiServer.py`: Main API server implementation
- `Tongue_crack_detection_model.py`: Model for detecting tongue cracks
- `jaggedScore.py`: Algorithm for calculating tongue edge jaggedness
- `tongue_papillae_analyzer.py`: Papillae detection and analysis
- `llmcall.py`: Integration with Gemini API for summary generation
- `segment.py`: Tongue segmentation functionality
- `output/`: Directory for storing generated images and analysis files

## Dependencies

- FastAPI: Web framework for the API
- OpenCV: Computer vision operations
- PyTorch: Deep learning framework for the SAM model
- NumPy: Numerical computing
- Pandas: Data analysis and manipulation
- Matplotlib: Visualization
- Segment Anything: Meta's segmentation model
- Roboflow: Initial tongue detection

## Notes

- The system requires an internet connection for the Roboflow API and Gemini API integration.
- Processing time may vary based on image quality and system specifications.
- GPU acceleration is highly recommended for optimal performance.
