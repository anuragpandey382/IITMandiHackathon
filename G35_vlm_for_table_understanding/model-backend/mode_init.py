import os
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers.pipelines import TextGenerationPipeline
import torch

MODEL_NAME = "meta-llama/Llama-3.2-1B"  

def load_llama3_pipeline():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, token="")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        token="",
        torch_dtype=torch.float16,
        device_map="auto"
    )
    return TextGenerationPipeline(model=model, tokenizer=tokenizer, max_new_tokens=512)