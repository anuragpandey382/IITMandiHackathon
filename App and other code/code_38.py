import os
import glob
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam

# --- GPU setup: enable memory growth so TF doesn’t grab all GPU RAM ---
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
print("Num GPUs Available:", len(gpus))

def load_magnitude_data(base_dir):
    """
    Scans base_dir/{fake,real} for CSVs, reads only the 'magnitude' column,
    and returns (X, y) where y=0 for fake, 1 for real.
    """
    X, y = [], []
    counts = {'fake': 0, 'real': 0}
    for label, cls in enumerate(['fake', 'real']):
        cls_path = os.path.join(base_dir, cls)
        print(f"→ Scanning {cls_path!r} for .csv files...")
        for csv_file in glob.glob(os.path.join(cls_path, '*.csv')):
            df = pd.read_csv(csv_file, usecols=['magnitude'])
            X.append(df['magnitude'].values)
            y.append(label)
            counts[cls] += 1
        print(f"   Loaded {counts[cls]} '{cls}' samples")
    X = np.array(X)
    y = np.array(y)
    print(f"Total loaded from {base_dir!r}: {len(X)} samples\n")
    return X, y

def build_model(input_dim):
    model = Sequential([
        Dense(1024, activation='relu', input_shape=(input_dim,)),
        Dropout(0.5),
        Dense(256, activation='relu'),
        Dropout(0.5),
        Dense(64, activation='relu'),
        Dropout(0.5),
        Dense(1, activation='sigmoid'),
    ])
    model.compile(
        optimizer=Adam(1e-3),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    return model

if __name__ == "__main__":
    # --- Load data ---
    print("=== LOADING TRAINING DATA ===")
    X_train, y_train = load_magnitude_data('./for-2sec/for-2seconds/training')
    print("=== LOADING VALIDATION DATA ===")
    X_val,   y_val   = load_magnitude_data('./for-2sec/for-2seconds/validation')
    print("=== LOADING TEST DATA ===")
    X_test,  y_test  = load_magnitude_data('./for-2sec/for-2seconds/testing')

    # --- Inspect shapes before scaling ---
    print(f"Shapes before scaling: X_train={X_train.shape}, X_val={X_val.shape}, X_test={X_test.shape}\n")

    # --- Scale features ---
    print("=== SCALING FEATURES ===")
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val   = scaler.transform(X_val)
    X_test  = scaler.transform(X_test)
    print("Scaling complete.\n")

    # --- Build & summarize model ---
    print("=== BUILDING MODEL ===")
    model = build_model(X_train.shape[1])
    model.summary()
    print()

    # --- Train on GPU if available ---
    print("=== STARTING TRAINING ===")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=20,
        batch_size=32,
        verbose=1  # show per-epoch progress bar
    )

    # --- Evaluate ---
    print("\n=== EVALUATING ON TEST SET ===")
    loss, acc = model.evaluate(X_test, y_test, verbose=1)
    print(f"Test Loss: {loss:.4f}, Test Accuracy: {acc:.4f}\n")

    # --- Save ---
    print("=== SAVING MODEL ===")
    model.save('voice_magnitude_classifier.h5')
    print("Model saved to voice_magnitude_classifier.h5")