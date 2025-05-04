#comment down plot funcs. and modify it according to you wanna access
import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from skimage.morphology import opening, closing, disk, remove_small_holes
from skimage.filters import threshold_otsu


def compute_and_plot_major_dents_concavity(
    image_path,
    r1=3,
    r2=3,
    A_max=64,
    sigma=18,
    sigma_green=3,
    concavity_thresh=-0.0145,
    length_thresh=10
):
    # Load and threshold
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh_val = threshold_otsu(gray)
    mask = (gray > thresh_val).astype(np.uint8)

    # Morphological cleaning
    mask_clean = opening(mask.astype(bool), disk(r1))
    mask_clean = closing(mask_clean, disk(r2)).astype(np.uint8)

    num_labels, labels = cv2.connectedComponents(mask_clean)
    if num_labels > 1:
        sizes = [np.sum(labels == i) for i in range(1, num_labels)]
        largest = 1 + int(np.argmax(sizes))
        mask_clean = (labels == largest).astype(np.uint8)

    mask_filled = remove_small_holes(mask_clean.astype(bool), area_threshold=A_max).astype(np.uint8)

    # Extract largest contour
    contours, _ = cv2.findContours(mask_filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contour = max(contours, key=cv2.contourArea).squeeze()
    x_vals, y_vals = contour[:, 0], contour[:, 1]

    # Find reference points (top-left, top-right, bottom)
    y_thresh = np.min(y_vals) + 0.2 * (np.max(y_vals) - np.min(y_vals))
    upper_indices = np.where(y_vals <= y_thresh)[0]
    top_left = contour[upper_indices[np.argmin(x_vals[upper_indices])]]
    top_right = contour[upper_indices[np.argmax(x_vals[upper_indices])]]
    bottom_y = np.max(y_vals)
    bottom_indices = np.where(y_vals == bottom_y)[0]
    bottom = contour[bottom_indices[np.argmin(np.abs(x_vals[bottom_indices] - np.median(x_vals)))]]


    def find_index(pt):
        return np.where((contour == pt).all(axis=1))[0][0]

    i_tl = find_index(top_left)
    i_tr = find_index(top_right)
    i_b = find_index(bottom)

    def arc_indices(start, end, N):
        if start <= end:
            return np.arange(start, end + 1)
        return np.concatenate([np.arange(start, N), np.arange(0, end + 1)])

    N = len(contour)
    path1 = arc_indices(i_tl, i_tr, N)
    path2 = arc_indices(i_tr, i_tl, N)
    seg_idx = path1 if i_b in path1 else path2

    # Extract segment and smooth
    segment = contour[seg_idx]
    xs, ys = segment[:, 0].astype(float), segment[:, 1].astype(float)
    xs_smooth = gaussian_filter1d(xs, sigma)
    ys_smooth = gaussian_filter1d(ys, sigma)
    xs_green = gaussian_filter1d(xs, sigma_green)
    ys_green = gaussian_filter1d(ys, sigma_green)

    # Compute concavity
    dx = np.gradient(xs_green)
    dy = np.gradient(ys_green)
    d2x = np.gradient(dx)
    d2y = np.gradient(dy)
    concavity = d2x + d2y

    # Count significant dents
    major_dent_count = 0
    is_in_dent = False
    dent_length = 0

    for i in range(1, len(xs_green) - 1):
        if concavity[i] < concavity_thresh:
            if not is_in_dent:
                dent_length = 1
                is_in_dent = True
            else:
                dent_length += 1
        else:
            if is_in_dent and dent_length >= length_thresh:
                major_dent_count += 1
            is_in_dent = False

    # Perimeter score
    def perimeter(xc, yc):
        return np.sum(np.hypot(np.diff(xc, append=xc[0]), np.diff(yc, append=yc[0])))

    P_red = perimeter(xs, ys)
    P_blue = perimeter(xs_smooth, ys_smooth)
    perimeter_score = 1 - (P_blue / P_red)

    # Plot
    plt.figure(figsize=(10, 10))
    plt.imshow(mask, cmap='gray')
    plt.plot(xs, ys, 'r-', linewidth=2, label="Original Red Segment")
    plt.plot(xs_smooth, ys_smooth, 'b--', linewidth=2, label="Smoothed Red Segment")
    plt.plot(xs_green, ys_green, 'g-', linewidth=2, label="Green Smoothed Segment")

    # Mark reference points
    for pt, txt in [(top_left, "Top-Left"), (top_right, "Top-Right"), (bottom, "Bottom")]:
        plt.plot(pt[0], pt[1], 'bo')
        plt.text(pt[0] + 3, pt[1], txt, color='blue', fontsize=9)

    plt.title(f"Contour with Major Dents (Dent Count: {major_dent_count})")
    plt.axis("equal")
    plt.legend()
    plt.show()

    return {
        'major_dent_count': major_dent_count,
        'perimeter_score': perimeter_score,
        'segment_contour': segment,
        'smoothed_segment': np.vstack((xs_smooth, ys_smooth)).T,
        'green_segment': np.vstack((xs_green, ys_green)).T
    }

if __name__ == "__main__":
    result = compute_and_plot_major_dents_concavity("tongue_output.jpg")
    print("Final Jagged score:", min(result['perimeter_score']*10, 8)+ result['major_dent_count'])
