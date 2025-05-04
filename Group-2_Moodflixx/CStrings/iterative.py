
import os
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
from typing import List
from pydantic import BaseModel, Field
class CharacteristicString(BaseModel):
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
    prompt_template = PromptTemplate.from_template("""
        You are a movie recommender assistant. Based on the following user preferences, generate {n} creative and emotionally resonant **characteristic strings**. 
        Each string should describe a *movie concept or theme* that matches the given inputs. Avoid specific movie names. Capture mood, tone, story arcs, and style that reflect the preferences.
        Limit each string to ~30 words. Return the output in **valid JSON format** as shown below:
        ```json
            {{
            "prompts": [
                {{ "prompt": "..." }},
                {{ "prompt": "..." }}
            ]
            }}```
         Each characteristic string should be a descriptive summary of the content type.\n\n
         User Preferences:\n
         - Mood: {mood}\n
         - Available Time/Runtime: {runtime}\n
         - Age Group: {age}\n
         - Preferred Genre: {genre}\n\n
         - You need a Plot Point similar to (if not any): {plot_point}\n
         Provide the response in the specified JSON format.
        
""")
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


def questions_to_cstring_iter(user_data, n, notincl):
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
    # prompt_template = PromptTemplate.from_template(
    #     "Based on the following user preferences, generate {n} detailed characteristic strings.\n"
    #     "Each string should describe a potential movie or show plot, theme, or scenario that fits the criteria.\n"
    #     "Focus on the narrative, atmosphere, and elements of the content.\n"
    #     "Please note that the described scenario, plot, movies, must cater to the people with the given mood and not necessarily entail such moods.\n"
    #     "Try to keep the content limited to 30 words.\n"
    #     "Do NOT include specific titles, character names, actors, directors, or any named entities.\n"
    #     "Also DO NOT generate stories of the form {notincl}\n"
    #     "Return output in the following JSON format:\n"
    #     '{\n  "prompts": [\n    {"prompt": "..."},\n    {"prompt": "..."}, ... ]\n}\n\n'
    #     "Each characteristic string should be a descriptive summary of the content type.\n\n"
    #     "User Preferences:\n"
    #     "- Mood: {mood}\n"
    #     "- Available Time/Runtime: {runtime}\n"
    #     "- Age Group: {age}\n"
    #     "- Preferred Genre: {genre}\n\n"
    #     "- You need a Plot Point similar to (if not any): {plot_point}\n"
    #     "Provide the response in the specified JSON format."
    # )
    prompt_template = PromptTemplate.from_template("""
        You are a movie recommender assistant. Based on the following user preferences, generate {n} creative and emotionally resonant **characteristic strings**. 
        Each string should describe a *movie concept or theme* that matches the given inputs. Avoid specific movie names. Capture mood, tone, story arcs, and style that reflect the preferences.
        Also DO NOT generate stories of the form {notincl}
        Limit each string to ~30 words. Return the output in **valid JSON format** as shown below:
        ```json
            {{
            "prompts": [
                {{ "prompt": "..." }},
                {{ "prompt": "..." }}
            ]
            }}```
         Each characteristic string should be a descriptive summary of the content type.\n\n
         User Preferences:\n
         - Mood: {mood}\n
         - Available Time/Runtime: {runtime}\n
         - Age Group: {age}\n
         - Preferred Genre: {genre}\n\n
         - You need a Plot Point similar to (if not any): {plot_point}\n
         Provide the response in the specified JSON format.
        
"""
    )
    structured_llm = llm.with_structured_output(Modelresponse)
    chain = (
        {
            "mood": RunnablePassthrough(),
            "runtime": RunnablePassthrough(),
            "age": RunnablePassthrough(),
            "genre": RunnablePassthrough(),
            "n": RunnablePassthrough(),
            "notincl":RunnablePassthrough(),
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
        "notincl":notincl,
        "plot_point":plot_point
    })
    return resp

def iterative_cstring_gen(user_data, n_iter = 3, cstring_per_iter = 5):

    resp = questions_to_cstring(user_data, cstring_per_iter)
    not_incl = ""
    total = []
    for _ in range(n_iter):
        if(_ == 0):
            not_incl = "\n"
            for i, cstring in enumerate(resp.prompts):
                not_incl += f"{cstring.prompt}\n"
                total.append(cstring)
        else:
            resp = questions_to_cstring_iter(user_data, cstring_per_iter, not_incl)
            not_incl = "\n"
            for i, cstring in enumerate(resp.prompts):
                not_incl += f"{cstring.prompt}\n"
                total.append(cstring)
    return total




                    
if __name__ == "__main__":
    # Sample usage
    user_data = {"mood": "Happy", "runtime": "2 hours", "age": "20", "genre": "Horror", "pp":"i want a kidnapping to happen in the movie"}
    n_characteristics = 10
    # resp = questions_to_cstring(user_data, n_characteristics)
    resp = iterative_cstring_gen(user_data, 3, 5)
    for i in resp:
        print(i)