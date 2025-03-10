

import os

# Check if the key is already defined in an environment variable
# This allows persistence between sessions without asking again
if 'GEMINI_API_KEY' in os.environ:
    Gemini_key = os.environ['GEMINI_API_KEY']
else:
    # Ask user for API key
    user_key = input("Please enter your Gemini API key: ")
    
    # Save to environment variable for future sessions
    os.environ['GEMINI_API_KEY'] = user_key
    
    # Also assign to the variable
    Gemini_key = user_key

# Now other files can continue to use config.Gemini_key as before
# Gemini_key="AIzaSyDB34rofMFLYfo0zwXnPZ6DLWHs3-I_rjM"

