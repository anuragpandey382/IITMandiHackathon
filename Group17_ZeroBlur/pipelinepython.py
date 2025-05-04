import numpy as np
import cv2

def detect_blur_laplacian(image, thresh=200):
    # Apply Gaussian blur to reduce noise
    image = cv2.GaussianBlur(image, (5, 5), 0)
    # Compute Laplacian
    laplacian = cv2.Laplacian(image, cv2.CV_64F, ksize=3)
    variance = np.var(laplacian)
    # Normalize by image standard deviation
    img_std = np.std(image)
    if img_std < 1e-6:  # Avoid division by near-zero
        return 0.0, True
    normalized_variance = variance / img_std
    if not np.isfinite(normalized_variance):
        normalized_variance = 0.0
    is_blurry = normalized_variance < thresh
    return normalized_variance, is_blurry

def detect_motion_between(prev_gray, gray, flow_threshold=1.0):
    if prev_gray is None:
        return False, 0.0
    flow = cv2.calcOpticalFlowFarneback(
        prev_gray, gray, None,
        pyr_scale=0.5, levels=3, winsize=15,
        iterations=3, poly_n=5, poly_sigma=1.2, flags=0
    )
    mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    mean_mag = np.mean(mag)
    return mean_mag > flow_threshold, mean_mag

def analyze_edges_and_brightness_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    edge_pixels = np.sum(edges > 0)
    total_pixels = edges.size
    edge_density = edge_pixels / total_pixels
    average_brightness = np.mean(gray)
    print(f"Edge Density: {edge_density:.4f}")
    print(f"Average Brightness: {average_brightness:.2f}")
    return edge_density, average_brightness

def extract_image_features(frame, prev_gray):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur_score, is_blurry = detect_blur_laplacian(gray)
    motion_detected, mean_flow = detect_motion_between(prev_gray, gray)
    edge_density, avg_brightness = analyze_edges_and_brightness_frame(frame)
    return {
        "blur_score": blur_score,
        "is_blurry": is_blurry,
        "motion_detected": motion_detected,
        "mean_flow": mean_flow,
        "edge_density": edge_density,
        "avg_brightness": avg_brightness
    }

# Ideal quality thresholds
IDEAL_BLUR = 200  # Normalized Laplacian variance
IDEAL_BRIGHTNESS = (0.4, 0.6)  # Normalized brightness range
FLOW_THRESHOLD = 1.0  # Optical flow mean magnitude for motion

def suggest_iso_shutter(mean_flow, brightness):
    suggestions = []
    if mean_flow > FLOW_THRESHOLD:
        suggestions.append("🔧 High motion → increase shutter speed (shorter exposure time).")
    if brightness < IDEAL_BRIGHTNESS[0]:
        suggestions.append("🔧 Too dark → increase ISO or use longer shutter speed.")
    elif brightness > IDEAL_BRIGHTNESS[1]:
        suggestions.append("🔧 Too bright → lower ISO or use shorter shutter speed.")
    if not suggestions:
        suggestions.append("✅ ISO and shutter speed are good.")
    return suggestions

def analyze_frame(frame, prev_frame, controller=None):
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY) if prev_frame is not None else None
    features = extract_image_features(frame, prev_gray)
    
    blur = features['blur_score']
    brightness = features['avg_brightness'] / 255.0
    mean_flow = features['mean_flow']
    edge_density = features['edge_density']
    
    dynamic_ideal_blur = IDEAL_BLUR * (1.5 if edge_density < 0.05 else 1.0)

    print(f"\n📊 Analysis:")
    print(f" - Blur Score: {blur:.3f} (Threshold: {dynamic_ideal_blur:.1f})")
    print(f" - Flow Score: {mean_flow:.3f} (Threshold: {FLOW_THRESHOLD:.1f})")
    print(f" - Brightness (normalized): {brightness:.3f}")
    
    suggestions = suggest_iso_shutter(mean_flow, brightness)
    for s in suggestions:
        print(s)

    quality_ok = (blur >= dynamic_ideal_blur) and (mean_flow <= FLOW_THRESHOLD) and \
                 (IDEAL_BRIGHTNESS[0] <= brightness <= IDEAL_BRIGHTNESS[1])

    if controller:
        new_iso, new_shutter = controller.update(blur, brightness, mean_flow)
        print(f"🔁 Updated Settings → ISO: {new_iso}, Shutter Speed: {new_shutter}")

    # Overlay text on frame
    frame_copy = frame.copy()
    cv2.putText(frame_copy, f"Blur: {blur:.3f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    cv2.putText(frame_copy, f"Flow: {mean_flow:.3f}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    cv2.putText(frame_copy, f"Brightness: {brightness:.3f}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    cv2.putText(frame_copy, f"Quality: {'Good' if quality_ok else 'Bad'}", (10, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if quality_ok else (0, 0, 255), 1)
    for i, s in enumerate(suggestions):
        cv2.putText(frame_copy, s, (10, 110 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

    return quality_ok, frame_copy, blur, brightness, mean_flow

class CameraFeedbackController:
    def __init__(self, initial_iso=400, initial_shutter=100):
        self.iso = initial_iso  # ISO units
        self.shutter = initial_shutter  # Milliseconds or camera-specific units
        self.history = []
        self.max_history = 10  # Limit history size

    def update(self, blur, brightness, mean_flow):
        self.history.append((blur, brightness, mean_flow))
        if len(self.history) > self.max_history:
            self.history.pop(0)  # Remove oldest entry
        
        if len(self.history) < 5:
            return self.iso, self.shutter

        recent = self.history[-5:]
        avg_blur = sum(x[0] for x in recent) / 5
        avg_brightness = sum(x[1] for x in recent) / 5
        avg_flow = sum(x[2] for x in recent) / 5

        # Adjust shutter speed for motion
        if avg_flow > FLOW_THRESHOLD:
            self.shutter = max(10, self.shutter - 10)
        elif avg_blur < IDEAL_BLUR:
            self.shutter = max(10, self.shutter - 5)

        # Adjust ISO for brightness
        if avg_brightness < IDEAL_BRIGHTNESS[0]:
            self.iso = min(3200, self.iso + 100)
        elif avg_brightness > IDEAL_BRIGHTNESS[1]:
            self.iso = max(100, self.iso - 100)

        return self.iso, self.shutter

def main():
    controller = CameraFeedbackController(initial_iso=400, initial_shutter=100)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    prev_frame = None
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break
            quality_ok, processed_frame, blur, brightness, mean_flow = analyze_frame(frame, prev_frame, controller)
            cv2.imshow("Camera Feedback", processed_frame)
            prev_frame = frame.copy()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()