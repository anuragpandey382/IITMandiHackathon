# # emotion_module.py
# import numpy as np
# import cv2
# from tensorflow.keras.models import load_model
# from keras.models import load_model
# from keras.models import Sequential
# from keras.layers import Dense, Conv2D, MaxPooling2D, Flatten, LSTM, Embedding,Dropout

# def build_model():
#     # Create the model
#     model = Sequential()

#     model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(48,48,1)))
#     model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
#     model.add(MaxPooling2D(pool_size=(2, 2)))
#     model.add(Dropout(0.25))

#     model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
#     model.add(MaxPooling2D(pool_size=(2, 2)))
#     model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
#     model.add(MaxPooling2D(pool_size=(2, 2)))
#     model.add(Dropout(0.25))

#     model.add(Flatten())
#     model.add(Dense(1024, activation='relu'))
#     model.add(Dropout(0.5))
#     model.add(Dense(7, activation='softmax'))
#     return model
# def run_emotion_detection():
#     model = build_model()  # Load trained model
#     model.load_weights('model.h5')
#     emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}
#     facecasc = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    
#     cap = cv2.VideoCapture(0)
#     emotion_log = []

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         faces = facecasc.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

#         for (x, y, w, h) in faces:
#             roi_gray = gray[y:y + h, x:x + w]
#             cropped_img = np.expand_dims(np.expand_dims(cv2.resize(roi_gray, (48, 48)), -1), 0)
#             prediction = model.predict(cropped_img)
#             maxindex = int(np.argmax(prediction))
#             emotion_log.append(emotion_dict[maxindex])
#             cv2.putText(frame, emotion_dict[maxindex], (x+20, y-60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

#         try:
#             cv2.imshow('Video', cv2.resize(frame, (960, 540)))
#         except cv2.error as e:
#             print("cv2.imshow failed on macOS. Exiting loop.")
#             break

#         if cv2.getWindowProperty('Video', cv2.WND_PROP_VISIBLE) < 1 or cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     cap.release()
#     cv2.destroyAllWindows()

#     # Return most frequent emotion
#     if emotion_log:
#         from collections import Counter
#         return Counter(emotion_log).most_common(1)[0][0]
#     else:
#         return "No emotion detected"
# emotion_module.py
import numpy as np
import cv2
from tensorflow.keras.models import load_model
from keras.models import load_model
from keras.models import Sequential
from keras.layers import Dense, Conv2D, MaxPooling2D, Flatten, LSTM, Embedding,Dropout
import matplotlib.pyplot as plt
from IPython import display


def build_model():
    # Create the model
    model = Sequential()

    model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(48,48,1)))
    model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Flatten())
    model.add(Dense(1024, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(7, activation='softmax'))
    return model
def run_emotion_detection():
    model = build_model()  # Load trained model
    model.load_weights('model.h5')
    emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}
    facecasc = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    
    cap = cv2.VideoCapture(0)
    emotion_log = []

    
    plt.ion()
    fig, ax = plt.subplots(figsize=(6, 4))
    img_display = ax.imshow(np.zeros((480, 640, 3), dtype=np.uint8))  # placeholder image
    plt.axis('off')
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = facecasc.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            roi_gray = gray[y:y + h, x:x + w]
            cropped_img = np.expand_dims(np.expand_dims(cv2.resize(roi_gray, (48, 48)), -1), 0)
            prediction = model.predict(cropped_img)
            maxindex = int(np.argmax(prediction))
            emotion_log.append(emotion_dict[maxindex])
            cv2.putText(frame, emotion_dict[maxindex], (x+20, y-60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        

        # Convert BGR to RGB for matplotlib
        rgb_frame = cv2.cvtColor(cv2.resize(frame, (640, 480)), cv2.COLOR_BGR2RGB)
        img_display.set_data(rgb_frame)
        display.display(plt.gcf())
        display.clear_output(wait=True)
        plt.pause(0.001)


    cap.release()
    cv2.destroyAllWindows()

    # Return most frequent emotion
    if emotion_log:
        from collections import Counter
        return Counter(emotion_log).most_common(1)[0][0]
    else:
        return "No emotion detected"
