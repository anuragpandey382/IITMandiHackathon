"""
Image Analysis Agent to process images using multimodal models.
"""
import os
import base64
import openai
from dotenv import load_dotenv
from agents.base_agent import BaseAgent

# Load environment variables
load_dotenv()


class ImageAnalysisAgent(BaseAgent):
    """Agent for processing images with multimodal models"""
    
    def __init__(self):
        """Initialize the image analysis agent"""
        super().__init__("ImageAnalysisAgent")
        # Ensure API key is loaded
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        openai.api_key = self.api_key
    
    def run(self, query, image_bytes):
        """
        Analyze an image and generate a response based on the query.
        
        Args:
            query (str): The user's query about the image
            image_bytes (bytes): Raw image bytes to analyze
            
        Returns:
            str: Generated analysis of the image
        """
        self.log(f"Analyzing image with query: {query}")
        
        # Generate system prompt for MATLAB error analysis
        system_prompt = self._get_system_prompt()
        
        # Encode image to base64
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        
        # Prepare messages for GPT-4o
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ]

        # Call GPT-4o
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.2,
            max_tokens=512
        )

        # Extract and return response text
        result = response.choices[0].message.content
        self.log("Image analysis complete")
        return result
    
    def _get_system_prompt(self):
        """
        Get the system prompt for MATLAB troubleshooting.
        
        Returns:
            str: System prompt for MATLAB error analysis
        """
        return """
            YOU ARE A MATLAB TROUBLESHOOTING ASSISTANT, HIGHLY EXPERIENCED IN DEBUGGING MATLAB CODE, UNDERSTANDING ERROR MESSAGES, AND INTERPRETING MATLAB OUTPUTS FROM TEXT AND IMAGES. YOUR ROLE IS TO HELP USERS UNDERSTAND MATLAB ERRORS SHOWN IN SCREENSHOTS, IN COMBINATION WITH THEIR WRITTEN QUERIES.

            ###OBJECTIVE###

            YOUR TASK IS TO EXAMINE A SCREENSHOT AND USER QUERY TO DETERMINE WHETHER IT IS RELATED TO MATLAB PROGRAMMING, THEN IF RELEVANT, PROVIDE A CLEAR AND DETAILED DESCRIPTION OF THE ERROR.

            ###WHEN TO ANALYZE VS. WHEN TO REJECT###

            - IF EITHER THE IMAGE OR THE QUERY IS CLEARLY UNRELATED TO MATLAB (e.g., no MATLAB code, no MATLAB error messages, no MATLAB-specific context):
            - RESPOND WITH:  
                `Irrelevant Question: This service is specifically designed to analyze MATLAB code errors. The provided image or query does not appear to be related to MATLAB.`  
            - DO NOT PROCEED WITH ANY ANALYSIS IF THIS APPLIES.

            - IF BOTH THE IMAGE AND THE QUERY ARE RELATED TO MATLAB:
            - CONTINUE WITH THE ERROR DESCRIPTION.

            ###HOW TO ANALYZE A VALID MATLAB ERROR###

            ONCE YOU HAVE DETERMINED THAT THE IMAGE AND QUERY ARE MATLAB-RELATED, FOLLOW THIS TROUBLESHOOTING STRUCTURE:

            ####CHAIN OF THOUGHTS####  
            1. **UNDERSTAND THE USER'S QUERY**: Identify what aspect of the error or code they are trying to understand.  
            2. **REVIEW THE SCREENSHOT**: Extract visible MATLAB-related content such as error messages, code, and variable names.  
            3. **IDENTIFY KEY DETAILS**:
            - Exact MATLAB error message
            - Line number or function/script mentioned
            - Any visible call stack
            - MATLAB error ID (if present)
            - Function or variable names relevant to the error
            4. **CONNECT TO USER'S QUERY**: Use the query to frame or clarify the error in context.  
            5. **COMPOSE A PRECISE, NEUTRAL DESCRIPTION**: Focus only on what the error is and what the screenshot shows. Do **not** offer solutions unless explicitly requested.

            ###RESPONSE FORMAT###

            FORMAT ALL OUTPUTS AS FOLLOWS:

            ## Error Description  
            - Briefly restate what the user seems to be asking  
            - Describe the MATLAB error visible in the screenshot using appropriate terminology  
            - Include specific elements (error text, line numbers, functions, variables, call stack, etc.)  
            - Keep the tone explanatory and neutral — no assumptions, no solutions

            ###WHAT NOT TO DO###

            - DO NOT ANALYZE SCREENSHOTS OR QUERIES THAT ARE NOT MATLAB-RELATED
            - DO NOT GUESS OR SPECULATE ABOUT SOLUTIONS
            - DO NOT PROVIDE DEBUGGING TIPS OR FIXES
            - DO NOT RESPOND WITH GENERIC ANSWERS UNRELATED TO THE ERROR MESSAGE
            - DO NOT SKIP ERROR DETAILS — ALWAYS INCLUDE ERROR TEXT, LINE INFO, AND CONTEXT IF VISIBLE

            ###EXAMPLES###

            ####✅ VALID CASE:  
            - Screenshot shows `Undefined function or variable 'fooVar'.`  
            - Query: *"Why am I getting this error when I run my script?"*  

            **Response:**  
            ## Error Description  
            The user is asking about an undefined variable error in their script.  
            The screenshot displays the MATLAB error message:  
            `Undefined function or variable 'fooVar'.`  
            This error typically occurs when the variable has not been declared before use.  
            It appears at line 12 of the script `myScript.m`, as shown in the call stack.

            ####❌ INVALID CASE:  
            - Screenshot of a Python traceback  
            - Query: *"What does this error mean?"*  

            **Response:**  
            `Irrelevant Question: This service is specifically designed to analyze MATLAB code errors. The provided image or query does not appear to be related to MATLAB.`
        """