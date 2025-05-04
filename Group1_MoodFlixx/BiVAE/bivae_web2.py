import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any
import traceback # Import traceback for better error logging

# --- Import your existing modules ---
# Ensure these modules load the model/data ONCE upon import or first use.
try:
    import convert
    import model
    MODEL_LOADED = True
    print("Model modules loaded successfully.")
    # Optional: Add any necessary one-time initialization for convert/model here
    # if it's not handled within the modules themselves upon import.
    # For example, if convert needs to load a title-to-ID map:
    # convert.load_title_map() # Assuming such a function exists

except ImportError as e:
    print(f"Error importing recommendation modules: {e}")
    print("API will run, but recommendation endpoint will fail.")
    MODEL_LOADED = False
except Exception as e:
    print(f"An unexpected error occurred during module import or model loading: {e}")
    traceback.print_exc() # Print full traceback for loading errors
    MODEL_LOADED = False
    # Depending on the error, you might want the app to exit instead.
    # raise e

# --- Define request and response models using Pydantic ---
class WatchlistRequest(BaseModel):
    # *** CHANGED: Keys are now strings (titles) instead of integers (IDs) ***
    watchlist: Dict[str, float] = Field(..., description="Dictionary of movie titles (str) to ratings (float)")
    num_recommendations: int = Field(25, gt=0, description="Number of recommendations to return")

class RecommendationResponse(BaseModel):
    recommendations: List[str] # Output remains a list of titles

# --- Create the FastAPI app instance ---
app = FastAPI(
    title="Movie Recommender API",
    description="Provides movie recommendations based on a user's watchlist (titles).",
    version="1.1.0", # Bump version for the change
)

# --- Your core recommendation logic (adapted for title input) ---
def get_recommendations_logic(watchlist_titles: Dict[str, float], num: int) -> List[str]:
    """
    Takes a watchlist (titles -> ratings) and number, returns movie title recommendations.
    Handles title-to-ID conversion and potential errors.
    """
    if not MODEL_LOADED:
         raise HTTPException(status_code=503, detail="Recommendation model service is unavailable.") # 503 might be more apt

    try:
        # --- NEW: Convert incoming titles to IDs ---
        print(f"Converting titles to IDs for watchlist: {list(watchlist_titles.keys())[:5]}...")
        try:
            # This is where your new conversion function is called
            watchlist_ids = convert.watchlist_titles_to_ids(watchlist_titles)
            print(f"Watchlist IDs obtained: {list(watchlist_ids.keys())[:5]}...")
        except KeyError as e:
            # Handle case where a title provided by the user is not found by the converter
            print(f"Error converting title to ID: Title '{e}' not found.")
            # Raise a 400 Bad Request because the input data is invalid
            raise HTTPException(status_code=400, detail=f"Invalid movie title provided: '{e}'")
        except Exception as e:
             # Catch other potential errors during conversion
             print(f"An unexpected error occurred during title conversion: {e}")
             traceback.print_exc()
             raise HTTPException(status_code=500, detail=f"Internal server error during title conversion: {type(e).__name__}")
        # --- END NEW ---

        # --- Proceed with the rest of the logic using the converted IDs ---
        print(f"Finding closest user for watchlist IDs: {list(watchlist_ids.keys())[:5]}...")
        closest = model.closest_user(watchlist_ids) # Use the watchlist with IDs
        print(f"Closest user ID found: {closest}")

        print(f"Getting {num} recommendation IDs for user {closest}...")
        recs = model.recommendation_ids(closest, num)
        print(f"Recommendation IDs: {recs}")

        print("Converting recommendation IDs back to titles...")
        # This part remains the same, converting recommended IDs to titles for the response
        titles = convert.titles_from_recs(recs)
        print(f"Recommended Titles: {titles}")

        imdbs = convert.imdb_from_recommendations(titles)

        return imdbs

    # --- Keep existing error handling for the model/recommendation part ---
    except AttributeError as e:
         print(f"AttributeError in recommendation logic: {e}. Check if 'model' or 'convert' modules loaded correctly and have the required functions.")
         traceback.print_exc()
         raise HTTPException(status_code=500, detail=f"Internal model error: Missing function or attribute - {e}")
    except KeyError as e:
         # This would now likely catch errors if recommendation_ids or titles_from_recs fails on an ID
         print(f"KeyError in recommendation logic (post-conversion): {e}. Likely an ID not found in model data.")
         raise HTTPException(status_code=404, detail=f"Data not found for internal ID: {e}")
    except Exception as e:
        # Catch other potential errors from your backend modules
        print(f"An unexpected error occurred in recommendation logic: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error during recommendation: {type(e).__name__}")


# --- Define the API endpoint ---
@app.post("/recommendations", response_model=RecommendationResponse)
async def create_recommendations(request: WatchlistRequest): # Uses the updated WatchlistRequest
    """
    Accepts a user's movie watchlist (titles -> ratings) and returns movie recommendations (titles).
    """
    print(f"Received request for {request.num_recommendations} recommendations.")
    try:
        # Pass the watchlist dictionary (titles -> ratings) directly
        titles = get_recommendations_logic(request.watchlist, request.num_recommendations)
        return RecommendationResponse(recommendations=titles)
    except HTTPException as e:
        # Re-raise HTTPExceptions directly (like the 400 from title conversion or 503/500/404 from logic)
        raise e
    except Exception as e:
        # Catch any unexpected error not already converted to HTTPException
         print(f"Unexpected error at endpoint level: {e}")
         traceback.print_exc()
         raise HTTPException(status_code=500, detail="An internal server error occurred.")

def agent_filter(titles):
    
def infer_emotion(user_input: str) -> str:
    """
    Uses the Gemini API to infer the primary emotion from user input.

    Args:
        user_input: The text sentence provided by the user.

    Returns:
        A single word representing the detected emotion, or an error message.
    """
    prompt = f"""
You are a recommendation checker agent.

Given a list of recommendations from system and set of watch history from user, check if the recommendations are correct and return the most relevant 4 recommendations. Do not add any movie/recommendations by yourself. Just filter from the ones we give you.

Text: "{user_input}"
""
    try:

        model = genai.GenerativeModel(model_name="gemini-2.0-flash")

        response = model.generate_content(contents=prompt)

        if response.parts:
            return response.text.strip()
        else:
            if response.prompt_feedback:
                 return f"Error: Blocked - {response.prompt_feedback}"
            return "Error: No content generated"

    except Exception as e:
        print(f"An error occurred during API call: {e}")
        return "Error: API request failed"


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Movie Recommender API. POST to /recommendations with {'watchlist': {'title': rating, ...}, 'num_recommendations': N}"}

# --- Run the server (when script is executed directly) ---
if __name__ == "__main__":
    print("Starting Uvicorn server...")
    # Make sure the module string "bivae_main_web:app" matches your filename and FastAPI instance name
    uvicorn.run("bivae_web2:app", host="127.0.0.1", port=8000, reload=True)
    # For production or access outside localhost (after considering security/deployment):
    # uvicorn.run("bivae_main_web:app", host="0.0.0.0", port=8000, reload=False)
