import cv2
import json
import base64
import numpy as np
import pandas as pd
from PIL import Image
from pathlib import Path
from ultralytics import YOLO
from paddleocr import PaddleOCR
from together import Together
from typing import List, Optional, Dict, Union

def detect_tables(image_path, model_path='best.pt', conf_thresh=0.5):
    model = YOLO(model_path)
    image = cv2.imread(image_path)  
    results = model(image, conf=conf_thresh)
    boxes = results[0].boxes.xyxy.cpu().numpy()
    return list(boxes)

class TextRecognizer:
    """
    A class for performing OCR on detected tables using PaddleOCR.
    
    Attributes:
        models_dir (Path): Directory containing OCR model files
    """
    
    def __init__(self, models_dir: Optional[Union[str, Path]] = None) -> None:
        """
        Initialize the TextRecognizer with model directory.
        
        Args:
            models_dir: Directory containing OCR model files
        """
        self.models_dir = Path(models_dir) if models_dir else Path(__file__).parent / 'paddleocr_models'
        self._setup_model_dirs()
        
        self.model = PaddleOCR(
            use_angle_cls=False,
            lang='en',
            det_model_dir=str(self.models_dir / 'det'),
            rec_model_dir=str(self.models_dir / 'rec')
        )

    def _setup_model_dirs(self) -> None:
        """Create necessary directories for model files."""
        (self.models_dir / 'det').mkdir(parents=True, exist_ok=True)
        (self.models_dir / 'rec').mkdir(parents=True, exist_ok=True)
        
    def recognize(
        self, 
        image_path: Union[str, Path], 
        table_boxes: Optional[np.ndarray] = None,
        padding: tuple = (0, 0)
    ) -> List[pd.DataFrame]:
        """
        Perform OCR on the image within specified table regions.
        
        Args:
            image_path: Path to the input image
            table_boxes: Array of table bounding box coordinates
            padding: Padding to add around table regions (x, y)
            
        Returns:
            List of DataFrames containing extracted text and positions
        """
        with Image.open(image_path) as img:
            img_array = np.array(img.convert('RGB'))
            
        if table_boxes is not None:
            if len(table_boxes) == 1:
                pad_x, pad_y = padding
                box = table_boxes[0]
                # Convert coordinates to integers
                x1, y1, x2, y2 = map(int, [box[0], box[1], box[2], box[3]])
                img_array = img_array[
                    max(y1-pad_y, 0):y2+pad_y,
                    max(x1-pad_x, 0):x2+pad_x
                ]
                ocr_result = self.model.ocr(img_array)
                return self._process_single_table(ocr_result[0])
            else:
                ocr_result = self.model.ocr(img_array)
                return self._process_multiple_tables(ocr_result[0], table_boxes)
        else:
            ocr_result = self.model.ocr(img_array)
            return self._process_single_table(ocr_result[0])

    def _process_multiple_tables(
        self, 
        ocr_data: List, 
        table_boxes: np.ndarray
    ) -> List[pd.DataFrame]:
        """Process OCR results for multiple tables."""
        result: Dict[int, List] = {}
        print("\n\n\n\nProcessing multiple tables...\n\n\n\n")
        for item in ocr_data:
            bbox = np.array(item[0]).astype(int)
            word = item[1][0]
            bbox = [bbox[:,0].min(), bbox[:,1].min(), bbox[:,0].max(), bbox[:,1].max()]
            
            for idx, table_box in enumerate(table_boxes):
                # Convert table_box coordinates to integers
                x1, y1, x2, y2 = map(int, [table_box[0], table_box[1], table_box[2], table_box[3]])
                if (bbox[0] >= x1 and bbox[1] >= y1 and 
                    bbox[0] <= x2 and bbox[1] <= y2):
                    if idx not in result:
                        result[idx] = []
                    result[idx].append((word, bbox))
                    
        return [
            pd.DataFrame(
                sorted(table_data, key=lambda x: (x[1][1], x[1][0])),
                columns=['text', 'boundingBox']
            )
            for table_data in result.values()
        ]
        
    def _process_single_table(self, ocr_data: List) -> List[pd.DataFrame]:
        """Process OCR results for a single table."""
        processed_data = [
            (item[1][0], [
                np.array(item[0])[:,0].min(),
                np.array(item[0])[:,1].min(),
                np.array(item[0])[:,0].max(),
                np.array(item[0])[:,1].max()
            ])
            for item in ocr_data
        ]
        
        return [pd.DataFrame(
            sorted(processed_data, key=lambda x: (x[1][1], x[1][0])),
            columns=['text', 'boundingBox']
        )]
    
def transform_results_to_dict(results):
    """
    Convert OCR results to a dictionary with native Python float values.
    """
    combined_data = {
        'text': [],
        'boundingBox': []
    }
    
    for table_df in results:
        if not isinstance(table_df, pd.DataFrame) or table_df.empty:
            continue
            
        # Extract text and convert bounding boxes to native Python types
        combined_data['text'].extend(table_df['text'].tolist())
        combined_data['boundingBox'].extend([
            [float(coord) for coord in bbox]  # Convert np.float64 to float
            for bbox in table_df['boundingBox']
        ])
    
    return combined_data

def create_csv(data, output_dir, i):
    headers = data.get('headers', [])
    rows = data.get('rows', [])
    
    max_cells = max(len(row) for row in rows) if rows else 0
    if headers:
        if len(headers) > max_cells:
            headers = headers[:max_cells]
        elif len(headers) < max_cells:
            headers = ['empty'] * (max_cells - len(headers)) + headers
    
    padded_rows = []
    for row in rows:
        if len(row) < max_cells:
            padded_row = [None] * (max_cells - len(row)) + row
            padded_rows.append(padded_row)
        else:
            padded_rows.append(row)
    
    df = pd.DataFrame(padded_rows, columns=headers if headers else None)
    csv_path = Path(output_dir) / f"csv_{i}.csv"
    df.to_csv(csv_path, index=False)

def save_cropped_table_image(original_image_path, table_box, output_path, padding=(5, 5)):
    """Save cropped image of the table based on bounding box coordinates."""
    pad_x, pad_y = padding
    img = cv2.imread(original_image_path)
    x1, y1, x2, y2 = map(int, [table_box[0], table_box[1], table_box[2], table_box[3]])
    
    cropped = img[
        max(y1-pad_y, 0):y2+pad_y,
        max(x1-pad_x, 0):x2+pad_x
    ]
    cv2.imwrite(output_path, cropped)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def run(image_path,j=0):
    table_boxes = detect_tables(image_path)
    table_count = len(table_boxes)
    if table_count == 0:
        print("No tables detected.")
        return 0
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Initialize Together client
    client = Together(api_key="d4601a91ae3986f319e3488f13561899e81a8cb1c6d4be37ff8f200fd4b3f6c7")
    for i, table_box in enumerate(table_boxes, 1):
        recognizer = TextRecognizer()
        results = recognizer.recognize(image_path, [table_box], padding=(5, 5))
        data = transform_results_to_dict(results)

        # Verify output
        print("Cleaned Output:")
        print({
            'text': data['text'],  # First 2 items for demo
            'boundingBox': data['boundingBox']
        })
    #     df = pd.DataFrame(data)
    #     extracted_data = df.to_dict('records')
    #     data_points_str = "\n".join(
    #         f"Text: '{item['text']}' | Position: {item['boundingBox']}" 
    #         for item in extracted_data
    #     )
        
    #     img_path = output_dir / f"image_{i+j}.jpg"
    #     save_cropped_table_image(image_path, table_box, img_path)
        
    #     base64_image = encode_image(f"output/image_{i+j}.jpg")
    #     response = client.chat.completions.create(
    #         model="meta-llama/Llama-4-Scout-17B-16E-Instruct",
    #         messages=[{
    #             "role": "user",
    #             "content": [
    #                     {
    #                         "type": "text",
    #                         "text": f"""Reconstruct this table from extracted data with coordinates:
                            
    #                         Data Points:
    #                         {data_points_str}
                            
    #                         Using the coordinates to determine rows/columns, output clean JSON with:
    #                         Make sure that the headers and number of cells in each row are equal.                       
    #                         {{
    #                             "headers": ["header1", ...],
    #                             "rows": [
    #                                 ["cell1", "cell2", ...],
    #                                 ...
    #                             ]
    #                         }}
    #                         ONLY include the final table structure."""
    #                     },
    #                     {
    #                         "type": "image_url",
    #                         "image_url": {
    #                             "url": f"data:image/jpeg;base64,{base64_image}",
    #                         }
    #                     }
    #                 ]
    #         }],
    #         response_format={"type": "json_object"},
    #         temperature=0.3,
    #     )
        
    #     json_str = response.choices[0].message.content
    #     data = json.loads(json_str)
        
    #     create_csv(data, output_dir, i+j)
        
    #     json_path = output_dir / f"json_{i+j}.json"
    #     with open(json_path, 'w') as f:
    #         json.dump(data, f, indent=2)
    
    # return table_count

if __name__ == "__main__":
    image_path = "test_4.png"
    run(image_path)