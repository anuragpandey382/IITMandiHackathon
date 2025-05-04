from .utils import TextToEmotion , TextToSemantic

def text(input_text):
    model1=TextToEmotion()
    model2 = TextToSemantic()
    if not input_text:
        input_text = input("Describe your mood in a sentence: ")
    text_mood_vector=model1(input_text)
    text_semantic_vector=model2(input_text)
    text_tagline_vector=model2(input_text)
    return text_mood_vector , text_semantic_vector, text_tagline_vector