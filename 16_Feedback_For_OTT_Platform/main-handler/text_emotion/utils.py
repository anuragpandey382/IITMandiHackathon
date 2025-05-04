from transformers import pipeline
from sentence_transformers import SentenceTransformer

class TextToEmotion:
    def __init__(self, model_name="j-hartmann/emotion-english-distilroberta-base"):
        self.model = pipeline("text-classification", model=model_name, top_k=None)
        self.emotion_map = {
            'anger': 0,
            'fear': 1,
            'joy': 2,
            'sadness': 3,
            'surprise': 4,
            'disgust': 5,
            'neutral': 6,
        }

    def __call__(self, text):
        model_output = self.model(text)
        return self._process_output(model_output)

    def _process_output(self, model_output):
        vector = [0.0] * 7
        for item in model_output[0]:  # Assuming batched input of size 1
            label = item['label'].lower()
            score = item['score']
            if label in self.emotion_map:
                vector[self.emotion_map[label]] += score
        return vector
    
    
class TextToSemantic:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def __call__(self, text):
        model_output = self.model.encode(text)
        return self._process_output(model_output)

    def _process_output(self, model_output):
        return model_output