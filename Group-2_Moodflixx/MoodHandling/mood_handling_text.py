
## We might try pre-trained model here to reduce calls to LLMs
import os
import json
from typing import List
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)
# Define prompt template
prompt_template = PromptTemplate.from_template(
    """
You are a movie mood assistant.

Given the following user form input as JSON, infer what 3 moods the user likely wants to experience from watching a movie.

Consider missing or empty fields as signs of user fatigue, low motivation, or indecisiveness. In such cases, suggest uplifting, relaxing, or easy-to-watch moods.

Output the result in this structured JSON format:

```json
{{
  "inferred_moods": ["mood1", "mood2", "mood3"],
  "reasoning": "Explain your inference in 1-2 lines"
}}
User Form Input:
{user_data}
"""
)

def infer_user_mood(user_data: dict) -> dict:
    # Build the prompt with user data
    formatted_prompt = prompt_template.invoke({
        "user_data": json.dumps(user_data, indent=2)
    })

    response = llm.invoke(formatted_prompt)
    try:
        start = response.content.find("{")
        end = response.content.rfind("}") + 1
        json_block = response.content[start:end]
        res = json.loads(json_block)
        return ','.join(res['inferred_moods'])
    except Exception as e:
        return {
            "error": "Failed to parse structured response",
            "raw_output": response.content,
            "exception": str(e),
        }

# Example usage
if __name__ == "__main__":
    user_input = {
        "mood": "",  
        "runtime": "2", 
        "age": "45", 
        "genre": "",  
    }

    print(infer_user_mood(user_data=user_input))
