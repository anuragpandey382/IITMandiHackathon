import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from skimage import morphology
from scipy.ndimage import distance_transform_edt
from scipy.special import softmax
from tqdm import tqdm
from collections import Counter
from multiprocessing import Pool

 
def skeletonize_image(binary_image):
    return morphology.skeletonize(binary_image // 255)

def find_branch_points(skel):
    return np.sum([
        np.sum(skel[i-1:i+2, j-1:j+2]) - 1 > 2
        for i in range(1, skel.shape[0]-1)
        for j in range(1, skel.shape[1]-1)
        if skel[i, j] == 1
    ])

def find_endpoints(skel):
    return np.sum([
        np.sum(skel[i-1:i+2, j-1:j+2]) - 1 == 1
        for i in range(1, skel.shape[0]-1)
        for j in range(1, skel.shape[1]-1)
        if skel[i, j] == 1
    ])

 
 
initial_weights = np.array([2.5, 2.0, 1.5, 3.25, 2.0, 1.0])
softmax_weights = softmax(initial_weights)

def extract_raw_features(image_path_and_name_tuple, resize_shape=(512, 512)):
    image_path, fname = image_path_and_name_tuple
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"❌ Cannot read: {image_path}")
        return None

    resized = cv2.resize(image, resize_shape)
    _, binary = cv2.threshold(resized, 127, 255, cv2.THRESH_BINARY)
    skel = skeletonize_image(binary)

    vein_length = np.sum(skel)
    dist = distance_transform_edt(binary)
    vein_width = np.mean(dist[binary == 255]) if np.any(binary == 255) else 0
    density = np.sum(binary == 255) / binary.size
    bp = find_branch_points(skel)
    ep = find_endpoints(skel)

    coords = np.column_stack(np.where(skel))
    tortuosity = vein_length / np.linalg.norm(coords[0] - coords[-1]) if len(coords) >= 2 else 1.0

    raw = np.array([density, bp, ep, tortuosity, vein_length, vein_width])
    return [fname, raw]

def extract_single_image_feature(image_path, scaler, resize_shape=(512, 512)):
    result = extract_raw_features((image_path, os.path.basename(image_path)), resize_shape)
    if result is None:
        return None
    raw_feat = result[1]
    raw_feat_norm = scaler.transform([raw_feat])
    return (raw_feat_norm * softmax_weights).flatten()

def process_2cluster_fixed_resize(dataset_path, test_image_paths=None, save_plot_path="2cluster_plot.png"):
    image_info_list = [
        (os.path.join(root, fname), fname)
        for root, _, files in os.walk(dataset_path)
        for fname in files if fname.endswith("_vessels.png")
    ]
    print(f"🔍 Found {len(image_info_list)} images")

    with Pool(16) as pool:
        raw_results = list(tqdm(pool.imap_unordered(extract_raw_features, image_info_list),
                                total=len(image_info_list), desc="⚙️ Extracting raw features"))

    raw_results = [r for r in raw_results if r]
    names = [r[0] for r in raw_results]
    raw_features = np.array([r[1] for r in raw_results])

     
    scaler = MinMaxScaler()
    normalized_features = scaler.fit_transform(raw_features)

     
    weighted_features = normalized_features * softmax_weights

     
    tsne = TSNE(n_components=2, random_state=42)
    X_tsne = tsne.fit_transform(weighted_features)

    kmeans = KMeans(n_clusters=2, random_state=42)
    labels = kmeans.fit_predict(weighted_features)

     
    cluster_counts = Counter(labels)
    print(f"\n📦 Cluster Distribution:")
    for cluster_id in range(2):
        print(f"  Cluster {cluster_id} → {cluster_counts[cluster_id]} images")

     
    plt.figure(figsize=(12, 9))
    scatter = plt.scatter(X_tsne[:, 0], X_tsne[:, 1], c=labels, cmap='coolwarm', s=80, alpha=0.8)
    for i, (x, y) in enumerate(X_tsne):
        plt.text(x, y, f"{labels[i]}", fontsize=8, ha='center', va='bottom', color='black')

    plt.title("2-Cluster Clustering with Softmax-Weighted Features")
    plt.xlabel("t-SNE Dimension 1")
    plt.ylabel("t-SNE Dimension 2")
    plt.colorbar(scatter, label="Cluster ID")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_plot_path)
    print(f"✅ Plot saved: {save_plot_path}")

     
    print("\n📋 Cluster assignments:")
    for name, label in zip(names, labels):
        print(f"{name} → Cluster {label}")

     
    if test_image_paths:
        print("\n🔎 Test Image Predictions:")
        for path in test_image_paths:
            fvec = extract_single_image_feature(path, scaler)
            if fvec is not None:
                pred = kmeans.predict([fvec])[0]
                print(f"🧪 {os.path.basename(path)} → Cluster {pred}")

 
if __name__ == "__main__":
    dataset_path = "/home/teaching/scelar/SBVPI files original/SBVPI"
    test_images = [
        "/home/teaching/scelar/SBVPI files original/SBVPI/1/1L_l_1_vessels.png",
        "/home/teaching/scelar/SBVPI files original/SBVPI/2/2L_l_1_vessels.png",
        "/home/teaching/scelar/SBVPI files original/SBVPI/4/4L_l_1_vessels.png",
        "/home/teaching/scelar/unet_d/debug_predictions/Eye1_prob_map.png"
    ]
    process_2cluster_fixed_resize(dataset_path, test_images)









