import json
import requests
from typing import Dict
from pathlib import Path
from together import Together
class InteractiveTableAnalyzer:
    def __init__(self, api_key: str, table_data: Dict):
        """
        Initialize with Together AI API key and table data.
        
        Args:
            api_key: Your Together AI API key
            table_data: Dictionary containing table data (headers and rows)
        """
        self.client = Together(api_key="3ce1c0fa4907dc04369e9f05a2663f11903001d8fa41778542db114ce6d6c74b")
        
        self.current_model = "deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"
        self.table_data = table_data
        
        self.conversation_history : List[Dict[str,str]]=[]
        self.system_prompt = """You are a precise table data analyst. Use ONLY the provided table data:

Table Structure:
Headers: {headers}

Data:
{rows_formatted}

Rules:
1. Answer strictly from the table
2. For calculations, show your work
3. Handle non-numeric values appropriately
4. Format dates as in table (e.g., Jan-20)
5. If data isn't available, say "I don't have that information in the table."
6. Be concise but complete"""

    def _format_rows(self) -> str:
        """Format table rows for the prompt."""
        return "\n".join(
            " | ".join(f"{self.table_data['headers'][i]}: {val}" 
                      for i, val in enumerate(row))
            for row in self.table_data["rows"]
        )
    
    def ask(self, question: str) -> str:
        """Ask a question about the table data."""
        try:
            # Prepare the initial messages
            messages = [
                {
                    "role": "system",
                    "content": self.system_prompt.format(
                        headers=", ".join(self.table_data["headers"]),
                        rows_formatted=self._format_rows()
                    )
                }
            ]
            
            # Add conversation history
            messages.extend(self.conversation_history)
            
            # Add the current question
            messages.append({"role": "user", "content": question})
            
            # Get the response
            response = self.client.chat.completions.create(
                model=self.current_model,
                messages=messages,
                temperature=0.1,
                max_tokens=512
            )
            
            answer = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            return answer
        except Exception as e:
            return f"Error processing your question: {str(e)}"

def load_table_data(file_path: str) -> Dict:
    """Load table data from JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Validate the table structure
        if not all(k in data for k in ["headers", "rows"]):
            raise ValueError("JSON must contain 'headers' and 'rows'")
        if len(data["headers"]) != len(data["rows"][0]):
            raise ValueError("Header count doesn't match row columns")
        
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {file_path} was not found")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in the data file")

def main():
    """Main interactive interface."""
    print("=== Table Data Analyzer ===")
    
    # Configuration - replace with your actual API key
    API_KEY = "3ce1c0fa4907dc04369e9f05a2663f11903001d8fa41778542db114ce6d6c74b"  # Replace with your Together AI API key
    DATA_FILE = "data.json"  # Path to your JSON data file
    
    # Load table data
    try:
        table_data = load_table_data(DATA_FILE)
        print(f"\nData loaded successfully from {DATA_FILE}")
        print(f"Available columns: {', '.join(table_data['headers'])}")
    except Exception as e:
        print(f"\nFailed to load table data: {str(e)}")
        return
    
    # Initialize analyzer
    analyzer = InteractiveTableAnalyzer(API_KEY, table_data)
    
    # Interactive Q&A loop
    print("\nEnter questions about the table data (type 'exit' to quit)")
    while True:
        question = input("\nYour question: ").strip()
        if question.lower() in ('exit', 'quit'):
            break
        
        if not question:
            print("Please enter a question")
            continue
        
        answer = analyzer.ask(question)
        print(f"\nAnswer: {answer}")
    
    print("\nGoodbye!")

if __name__ == "__main__":
    main()