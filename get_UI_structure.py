import os
import google.generativeai as genai
from conf import Gemini_key

def get_directory_structure():
    """
    Traverses the UI assets directory and creates a text representation of its structure.
    
    Returns:
        str: A string representing the directory structure
    """
    root_dir = r"C:\Users\user\My project (2)\Assets\Resources\UIs"
    structure = ""

    def traverse_directory(directory, indent=""):
        nonlocal structure
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                # Add folder to the structure
                structure += f"{indent}|----->{item}\\\n"
                # Recurse into subdirectory
                traverse_directory(item_path, indent + "      ")
            elif os.path.isfile(item_path) and item.lower().endswith(".png"):
                # Add .png file to the structure
                structure += f"{indent}|------>{item}\n"

    traverse_directory(root_dir)
    return structure

def read_brainstorm_file():
    """
    Reads the content of brainstorm.md file.
    
    Returns:
        str: Content of the brainstorm.md file
    """
    try:
        with open('brainstorm.md', 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print("Warning: brainstorm.md file not found. Using empty string.")
        return ""

def get_gemini_ui_suggestion():
    """
    Generates a UI suggestion based on directory structure and brainstorm content.
    
    Returns:
        str: Gemini's generated UI suggestion
    """
    try:
        # Get directory structure and brainstorm content
        brainstorm = read_brainstorm_file()
        directory_structure = get_directory_structure()
        
        # Prepare the prompt
        prompt = fr"""you are a senior game designer , you have to design the structure of a game based on the available assets , here is the structure of the assets and the brainstorming results , you should create the best structure of the game , levels, and story based on the UI assets available , here is some explanation:
You have the path of a Folder with UI assets for mini games , the path is [\Assets\Resources\UIs], you should create the best structure of the game , levels, and story based on the UI assests disponible , here is some expanation:
1- the folder [alphabetics_and_numbers] have many UI assets for numbers and alphabetics in styles in each folder
2- animals have pictures of animals
3- Bunny_animation have animations for a pixelated bunny
4- the folder [goldGUIHMbars] have some elements you can know what each one is from the names.
5- the folder [Jungle-GUI-PNG] have assets for a jungle UI
6- the folder [UI] have some UI elements you can know them based on the names
7- the folder [UI_World_Flags_By_verzatiledev] have png on flags
NOTE : based of the names on png files and the description of the folders i gave you , you should create the best UI possible , the assets are 2D.
NOTE : you have to give path for every assets used , for example , you should tell how many button should be used , the path of all button you want to use , the font used (it should be exist in unity 3D),the position of each item , the size of each item , the color of text , what each button should done after click on it , and all of these things
mwntion the whole path of the aasets used in your report , not only the name of the asset
brainstorming results (You may change them bc they are not based on the available assests):
{brainstorm}
the structure of the assets:
{directory_structure}
This is the path of the UI assets : [....\Assets\Resources\UIs]
the GUI we need are :
- Menu with the background , a table , and buttons
- Levels wtih background , buttons (If needed), charachters ,...etcS

This time i want you to focus on creating the design for only the first level and the menu
"""
        # Configure and generate response
        genai.configure(api_key=Gemini_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        
        # Save the response to UI_suggestion.md
        with open('UI_suggestion.md', 'w', encoding='utf-8') as file:
            file.write(response.text)
        
        print("\033[92mUI structure suggestions generated and saved to UI_suggestion.md\033[0m")
        return response.text
    
    except Exception as e:
        error_msg = f"Error generating UI suggestions: {str(e)}"
        print(f"\033[91m{error_msg}\033[0m")
        return error_msg