

import os

if 'GEMINI_API_KEY' in os.environ:
    Gemini_key = os.environ['GEMINI_API_KEY']
else:
    # Ask user for API key
    user_key = input("Please enter your Gemini API key: ")
    
    # Save to environment variable for future sessions
    os.environ['GEMINI_API_KEY'] = user_key
    
    # Also assign to the variable
    Gemini_key = user_key



