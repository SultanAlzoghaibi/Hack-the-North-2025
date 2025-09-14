import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_openai_response(input_string, max_tokens=256, temperature=0.7):

    try:
        # Set up OpenAI API key from environment
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai.api_key:
            return "Error: OPENAI_API_KEY not found in environment variables"
        
        if not input_string or not input_string.strip():
            return "Error: Input string is empty"
        
        # Create the message for ChatGPT
        messages = [
            {
                "role": "user",
                "content": input_string.strip()
            }
        ]
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Extract and return the response text
        result = response.choices[0].message.content
        return result
        
    except Exception as e:
        return f"Error calling OpenAI API: {str(e)}"

# Example usage function
def test_openai_function():
    """Test the OpenAI function with a sample input"""
    test_input = "Hello, how are you today?"
    response = get_openai_response(test_input)
    print(f"Input: {test_input}")
    print(f"Response: {response}")

if __name__ == "__main__":
    test_openai_function()
