from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers.pipelines import TextGenerationPipeline
import os
import torch
import pandas as pd

MODEL_NAME = "meta-llama/Llama-3.2-1B" 

def load_llama3_pipeline():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, token=os.getenv("HF_TOKEN"))
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        token=os.getenv("HF_TOKEN"),
        torch_dtype=torch.float16,
        device_map="auto"
    )

    return TextGenerationPipeline(model=model, tokenizer=tokenizer, max_new_tokens=512)


def ask_llama3_about_functions(llm_pipeline, function_text, csv_file, user_query) :
    df = pd.read_csv(csv_file, on_bad_lines='skip')
    df = df.fillna('')

    prompt = f""" You are a helpful assistant for writing Python codes and functions. 
        You also have capabilities to understand tables and dataframes.
        You have to read this dataframe {df} and understand the data in it.
        Write a python code to implement the function {function_text}
        """
    
    