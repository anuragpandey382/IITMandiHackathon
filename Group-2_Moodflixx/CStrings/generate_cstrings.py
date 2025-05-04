import os
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from typing import List
from pydantic import BaseModel, Field



class CharacteristicString(BaseModel):
    # The description here is important to guide the LLM
    prompt : str = Field(description="Detailed characteristic string describing a potential movie or show plot/theme based on user preferences. Avoid specific titles or character names.")

class Modelresponse(BaseModel):
    prompts : List[CharacteristicString] = Field(description="A list of characteristic strings describing potential entertainment content.")


def questions_to_cstring(user_data, n):
    mood = user_data.get('mood', 'neutral') 
    # language = user_data.get('language', 'any')
    genre = user_data.get('genre', 'any')
    runtime = user_data.get('runtime', 'any')
    age_group = user_data.get('age', 'any')
    # year = user_data.get('year', 'any')
    # actor = user_data.get('actors', 'any') ## KB Does not need specifities
    plot_point = user_data.get('pp', 'any')

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    # Enhanced Prompt Template
    prompt_template = PromptTemplate.from_template(
        "Based on the following user preferences, generate {n} detailed characteristic strings. "
        "Each string should describe a potential movie or show plot, theme, or scenario that fits the criteria. "
        "Focus on the narrative, atmosphere, and elements of the content. "
        "Please note that the described scenario, plot, movies, must cater to the people with the given mood and not necessarily entail such moods. "
        "Try to Keep the content limited to 30 words"
        "Do NOT include specific titles, character names, actors, directors, or any named entities. "
        "Each characteristic string should be a descriptive summary of the content type.\n\n"
        "User Preferences:\n"
        "- Mood: {mood}\n"
        "- Available Time/Runtime: {runtime}\n"
        "- Age Group: {age}\n"
        "- Preferred Genre: {genre}\n"
        "- You need a Plot Point similar to (if not any): {plot_point}\n"
        "Provide the response in the specified JSON format."
    )
    structured_llm = llm.with_structured_output(Modelresponse)
    chain = (
        {
            "mood": RunnablePassthrough(),
            "runtime": RunnablePassthrough(),
            "age": RunnablePassthrough(),
            "genre": RunnablePassthrough(),
            "n": RunnablePassthrough(),
            "plot_point":RunnablePassthrough()
        }
        | prompt_template
        | structured_llm
    )

    resp = chain.invoke({
        "mood": mood,
        "runtime": runtime,
        "age": age_group,
        "genre": genre,
        "n": n,
        "plot_point":plot_point
    })
    return resp


if __name__ == "__main__":
    # Sample usage
    user_data = {"mood": "Happy", "runtime": "2 hours", "age": "20", "genre": "Horror"}
    n_characteristics = 10
    resp = questions_to_cstring(user_data, n_characteristics)
    print(f"Generated {len(resp.prompts)} Characteristic Strings:")
    for i, char_string in enumerate(resp.prompts):
        print(f"{char_string.prompt}")

