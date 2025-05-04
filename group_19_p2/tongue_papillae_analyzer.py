import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage
from skimage import morphology, measure, segmentation, color, filters
import pandas as pd

class TonguePapillaeAnalyzer:
    """
    minor change
    Class for analyzing tongue images to detect papillae size and redness in local patches.
    """
    
    def __init__(self, patch_size=50, threshold_adjust=1.0, min_papillae_size=10, 
                 max_papillae_size=500, contrast_enhance=1.5):
        """
        Initialize the analyzer with parameters.
        
        Args:
            patch_size: Size of local patches for analysis
            threshold_adjust: Factor to adjust thresholding sensitivity
            min_papillae_size: Minimum size of papillae in pixels
            max_papillae_size: Maximum size of papillae in pixels
            contrast_enhance: Factor for contrast enhancement
        """
        self.patch_size = patch_size
        self.threshold_adjust = threshold_adjust
        self.min_papillae_size = min_papillae_size
        self.max_papillae_size = max_papillae_size
        self.contrast_enhance = contrast_enhance

    def preprocess_image(self, image):
        """
        Preprocess the tongue image for better analysis.
        
        Args:
            image: Input tongue image
            
        Returns:
            Preprocessed image
        """
        # Convert to RGB if grayscale
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        # Convert to LAB color space (better for redness detection)
        lab_image = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        
        # Apply contrast enhancement
        l, a, b = cv2.split(lab_image)
        clahe = cv2.createCLAHE(clipLimit=self.contrast_enhance, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Reconstruct image
        enhanced_lab = cv2.merge([l, a, b])
        enhanced_rgb = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoisingColored(enhanced_rgb, None, 10, 10, 7, 21)
        
        return denoised

    def detect_papillae_in_patch(self, patch):
        """
        Detect papillae in a local patch of the tongue.
        
        Args:
            patch: Local patch of the tongue image
            
        Returns:
            Labeled papillae, properties of detected papillae
        """
        # Convert to grayscale if RGB
        if len(patch.shape) == 3:
            gray_patch = cv2.cvtColor(patch, cv2.COLOR_RGB2GRAY)
        else:
            gray_patch = patch
            
        # Use adaptive thresholding to identify potential papillae
        thresh = cv2.adaptiveThreshold(
            gray_patch, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, self.threshold_adjust * 2
        )
        
        # Remove small noise
        cleaned = morphology.remove_small_objects(
            thresh.astype(bool), min_size=self.min_papillae_size
        )
        
        # Apply distance transform to separate close papillae
        dist_transform = ndimage.distance_transform_edt(cleaned)
        
        # Find local maxima
        local_max = filters.rank.maximum(dist_transform.astype(np.uint8), morphology.disk(2))
        markers = ndimage.label(local_max == dist_transform)[0]
        
        # Apply watershed segmentation
        segmented = segmentation.watershed(-dist_transform, markers, mask=cleaned)
        
        # Measure properties
        props = measure.regionprops(segmented, intensity_image=gray_patch)
        
        return segmented, props

    def analyze_redness(self, patch, segmented):
        """
        Analyze redness of detected papillae in a patch.
        
        Args:
            patch: Local patch of the tongue image
            segmented: Segmentation mask from the papillae detection
            
        Returns:
            Average redness values for each papillae
        """
        # Convert to LAB color space
        if len(patch.shape) == 3:
            lab_patch = cv2.cvtColor(patch, cv2.COLOR_RGB2LAB)
            hsv_patch = cv2.cvtColor(patch, cv2.COLOR_RGB2HSV)
        else:
            # If the patch is grayscale, convert to RGB first
            rgb_patch = cv2.cvtColor(patch, cv2.COLOR_GRAY2RGB)
            lab_patch = cv2.cvtColor(rgb_patch, cv2.COLOR_RGB2LAB)
            hsv_patch = cv2.cvtColor(rgb_patch, cv2.COLOR_RGB2HSV)
        
        # Extract the a channel (red-green) and hue, saturation
        a_channel = lab_patch[:, :, 1]  # Higher values indicate more redness
        h_channel = hsv_patch[:, :, 0]  # Hue
        s_channel = hsv_patch[:, :, 1]  # Saturation
        
        # Calculate redness for each papillae
        redness_values = []
        
        unique_labels = np.unique(segmented)
        unique_labels = unique_labels[unique_labels != 0]  # Exclude background
        
        for label in unique_labels:
            # Create mask for this papilla
            papilla_mask = segmented == label
            
            # Measure average a-channel value (higher = more red)
            a_avg = np.mean(a_channel[papilla_mask])
            
            # Calculate normalized redness metric
            # (considering both a-channel and saturation)
            h_avg = np.mean(h_channel[papilla_mask])
            s_avg = np.mean(s_channel[papilla_mask])
            
            # Create a redness metric - higher values for more red papillae
            # Red is around 0-30 in hue space
            h_factor = 1.0
            if 0 <= h_avg <= 30 or 330 <= h_avg <= 360:
                h_factor = 2.0  # Boost redness score for red hues
                
            redness_score = (a_avg + 128) / 255 * s_avg / 255 * h_factor
            
            redness_values.append({
                'label': label,
                'a_channel': a_avg,
                'hue': h_avg,
                'saturation': s_avg,
                'redness_score': redness_score
            })
            
        return redness_values

    def extract_patches(self, image, mask):
        """
        Extract local patches from the tongue image for analysis.
        Only extracts patches that are fully within the tongue region.
        
        Args:
            image: Input tongue image
            mask: Tongue mask
            
        Returns:
            List of patches and their coordinates
        """
        patches = []
        coords = []
        
        height, width = mask.shape[:2]
        
        # Find bounding box of the tongue to focus only on relevant areas
        non_zero_points = cv2.findNonZero(mask)
        if non_zero_points is None:
            return [], []  # No tongue detected
            
        x, y, w, h = cv2.boundingRect(non_zero_points)
        
        # Only analyze within the bounding box (with small margin)
        margin = 5
        x_start = max(0, x - margin)
        y_start = max(0, y - margin)
        x_end = min(width, x + w + margin)
        y_end = min(height, y + h + margin)
        
        # Extract patches with overlap
        for y_pos in range(y_start, y_end - self.patch_size + 1, self.patch_size // 2):
            for x_pos in range(x_start, x_end - self.patch_size + 1, self.patch_size // 2):
                patch = image[y_pos:y_pos+self.patch_size, x_pos:x_pos+self.patch_size]
                patch_mask = mask[y_pos:y_pos+self.patch_size, x_pos:x_pos+self.patch_size]
                
                # Only include patches that are mostly tongue (at least 70% of the patch)
                mask_coverage = np.sum(patch_mask > 0) / (self.patch_size * self.patch_size)
                if mask_coverage > 0.7:
                    patches.append(patch)
                    coords.append((x_pos, y_pos))
        
        return patches, coords

    def analyze_image_with_mask(self, image, mask):
        """
        Analyze a tongue image using an external mask.
        
        Args:
            image: Tongue image (RGB)
            mask: Binary mask of the tongue region
            
        Returns:
            DataFrame with papillae measurements and visualization images
        """
        # Preprocess
        preprocessed = self.preprocess_image(image)
        
        # Create a visualization of the tongue segmentation with contour outline
        segmentation_viz = image.copy()
        
        # Find contours of the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Draw contour on the original image in green with 2px thickness
        cv2.drawContours(segmentation_viz, contours, -1, (0, 255, 0), 2)
        
        # Apply mask to get segmented tongue
        segmented_tongue = cv2.bitwise_and(preprocessed, preprocessed, mask=mask)
        
        # Extract patches
        patches, coords = self.extract_patches(segmented_tongue, mask)
        
        # Process each patch
        results = []
        visualization = image.copy()
        
        # Create a separate patch visualization
        patch_viz = image.copy()
        
        for i, (patch, (x, y)) in enumerate(zip(patches, coords)):
            # Detect papillae
            segmented, props = self.detect_papillae_in_patch(patch)
            
            if len(props) == 0:
                continue
                
            # Analyze redness
            redness_data = self.analyze_redness(patch, segmented)
            
            # Store results
            for j, prop in enumerate(props):
                if self.min_papillae_size <= prop.area <= self.max_papillae_size:
                    # Find corresponding redness data
                    red_data = next((r for r in redness_data if r['label'] == prop.label), None)
                    
                    if red_data:
                        results.append({
                            'patch_id': i,
                            'papilla_id': j,
                            'x': x + prop.centroid[1],
                            'y': y + prop.centroid[0],
                            'size': prop.area,
                            'perimeter': prop.perimeter,
                            'eccentricity': prop.eccentricity,
                            'redness_score': red_data['redness_score'],
                            'a_channel': red_data['a_channel'],
                            'hue': red_data['hue'],
                            'saturation': red_data['saturation']
                        })
            
            # Visualize this patch on the patch visualization with a thin border
            cv2.rectangle(patch_viz, (x, y), (x+self.patch_size, y+self.patch_size), (0, 255, 0), 1)
        
        # Create dataframe
        df = pd.DataFrame(results)
        
        return df, visualization, segmentation_viz, patch_viz

    def analyze_image(self, image_path):
        """
        Legacy method to analyze a tongue image from file path.
        Now uses the SAM model segmentation from the FastAPI app.
        
        Args:
            image_path: Path to the tongue image
            
        Returns:
            DataFrame with papillae measurements and visualization images
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")
            
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize if image is too large
        max_dim = 800
        if max(image.shape[:2]) > max_dim:
            scale = max_dim / max(image.shape[:2])
            image = cv2.resize(image, None, fx=scale, fy=scale)
        
        # Create a simple mask for the whole image (for compatibility)
        # In actual use, this will be replaced by the mask from SAM
        mask = np.ones((image.shape[0], image.shape[1]), dtype=np.uint8) * 255
        
        # Use the analyze_image_with_mask method
        return self.analyze_image_with_mask(image, mask)

    def visualize_results(self, image, df):
        """
        Visualize the detected papillae and their properties.
        
        Args:
            image: Original image
            df: DataFrame with papillae measurements
            
        Returns:
            Visualization image
        """
        # Create a copy for visualization
        viz_image = image.copy()
        
        # Define color map for redness (blue to red)
        if len(df) > 0:
            min_redness = df['redness_score'].min()
            max_redness = df['redness_score'].max()
            redness_range = max_redness - min_redness
            
            # Draw circles for each papilla
            for _, row in df.iterrows():
                x, y = int(row['x']), int(row['y'])
                size = int(np.sqrt(row['size'] / np.pi))
                
                # Normalize redness score
                if redness_range > 0:
                    norm_redness = (row['redness_score'] - min_redness) / redness_range
                else:
                    norm_redness = 0.5
                
                # Create color (blue to red)
                color = (int(255 * (1 - norm_redness)), 0, int(255 * norm_redness))
                
                # Draw the papilla
                cv2.circle(viz_image, (x, y), max(1, size), color, 1)
        
        return viz_image

    def generate_report(self, df):
        """
        Generate a statistical report of the papillae analysis.
        
        Args:
            df: DataFrame with papillae measurements
            
        Returns:
            Dictionary with statistical metrics
        """
        if len(df) == 0:
            return {
                'total_papillae': 0,
                'avg_size': 0,
                'avg_redness': 0,
                'patch_density': 0,
                'high_redness_patches': [],
                'high_redness_values': []
            }
            
        # Calculate statistics
        total_papillae = len(df)
        avg_size = df['size'].mean()
        avg_redness = df['redness_score'].mean()
        
        # Group by patch
        patch_stats = df.groupby('patch_id').agg({
            'size': 'mean',
            'redness_score': 'mean',
            'papilla_id': 'count'
        }).rename(columns={'papilla_id': 'count'})
        
        # Find patches with highest redness
        high_redness_patches = patch_stats.sort_values('redness_score', ascending=False).head(3)
        
        # Prepare report
        report = {
            'total_papillae': total_papillae,
            'avg_size': avg_size,
            'avg_redness': avg_redness,
            'patch_density': patch_stats['count'].mean(),
            'high_redness_patches': high_redness_patches.index.tolist(),
            'high_redness_values': high_redness_patches['redness_score'].tolist()
        }
        
        return report