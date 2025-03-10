
import conf as config
import process
import asyncio
import os
from Agents import Brainstorm
from docx import Document 
import subprocess
import platform

GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"


def read_brainstorm_file():
    """Read the content of the brainstorm.md file if it exists"""
    try:
        if os.path.exists("brainstorm.md"):
            with open("brainstorm.md", "r", encoding="utf-8") as file:
                return file.read()
        return ""
    except Exception as e:
        print(f"{RED}Error reading brainstorm file: {str(e)}{RESET}")
        return ""

def extract_text_from_docx(file_path):
    """Extract text from a Word document using python-docx"""
    try:
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        print(f"{RED}Error reading Word document: {str(e)}{RESET}")
        return None

def open_file_browser_dialog():
    """Open a file browser dialog that works across platforms"""
    file_path = None
    
    try:
        if platform.system() == "Windows":
            # PowerShell approach for Windows
            powershell_cmd = """
            Add-Type -AssemblyName System.Windows.Forms
            $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
            $openFileDialog.Filter = "Word Documents (*.docx)|*.docx|All Files (*.*)|*.*"
            $openFileDialog.Title = "Select a Word Document"
            $openFileDialog.ShowDialog() | Out-Null
            $openFileDialog.FileName
            """
            result = subprocess.run(["powershell", "-Command", powershell_cmd], capture_output=True, text=True)
            file_path = result.stdout.strip()
        elif platform.system() == "Darwin":  # macOS
            # AppleScript for macOS
            script = """
            osascript -e 'tell application "System Events"
                activate
                set filePath to choose file with prompt "Select a Word Document" of type {"docx"}
                POSIX path of filePath
            end tell'
            """
            result = subprocess.run(script, shell=True, capture_output=True, text=True)
            file_path = result.stdout.strip()
        else:  # Linux and others
            # Try using zenity if available
            try:
                result = subprocess.run(
                    ["zenity", "--file-selection", "--title=Select a Word Document", "--file-filter=*.docx"], 
                    capture_output=True, 
                    text=True
                )
                file_path = result.stdout.strip()
            except FileNotFoundError:
                print(f"{YELLOW}Could not find a graphical file dialog tool. Please provide the file path manually.{RESET}")
                return None
    except Exception as e:
        print(f"{RED}Error opening file dialog: {str(e)}{RESET}")
        return None
    
    # Check if a file was actually selected
    if not file_path or not os.path.isfile(file_path):
        return None
        
    return file_path

async def main():
    print(f"{GREEN}==== Unity Game Development System ===={RESET}")
    print(f"{GREEN}Choose an option:{RESET}")
    print(f"{GREEN}1. Create a new Unity game (Generate all scripts from scratch){RESET}")
    print(f"{GREEN}2. Edit an existing Unity game (Modify existing CS files){RESET}")

    choice = input(f"{GREEN}Enter your choice (1 or 2): {RESET}").strip()

    if choice == "1":
        print(f"{GREEN}Creating a new Unity game...{RESET}")
        
        # Ask user if they want to upload a Word document
        print(f"{BLUE}Would you like to upload a Word document with your game description? (yes/no){RESET}")
        upload_choice = input(f"{BLUE}> {RESET}").strip().lower()
        
        game_subject = ""
        
        if upload_choice == "yes":
            print(f"{GREEN}Opening file browser... Please select a Word document.{RESET}")
            file_path = open_file_browser_dialog()
            
            if file_path:
                print(f"{GREEN}File selected: {file_path}{RESET}")
                file_content = extract_text_from_docx(file_path)
                
                if file_content:
                    game_subject = file_content
                    print(f"{YELLOW}Extracted content summary: {game_subject[:100]}...{RESET}")
                    
                    # Ask if the user wants to review or modify the extracted content
                    print(f"{BLUE}Would you like to review or modify the extracted content? (yes/no){RESET}")
                    review_choice = input(f"{BLUE}> {RESET}").strip().lower()
                    
                    if review_choice == "yes":
                        print(f"{BLUE}Current content:{RESET}")
                        print(f"{CYAN}{game_subject}{RESET}")
                        print(f"{BLUE}Enter modified content (or press Enter to keep as is):{RESET}")
                        modified_content = input(f"{BLUE}> {RESET}").strip()
                        
                        if modified_content:
                            game_subject = modified_content
                else:
                    print(f"{RED}Failed to extract content from the file.{RESET}")
                    print(f"{BLUE}Please describe your game idea manually:{RESET}")
                    game_subject = input(f"{BLUE}> {RESET}").strip()
            else:
                print(f"{RED}No file was selected or the file dialog could not be opened.{RESET}")
                print(f"{BLUE}Please describe your game idea manually:{RESET}")
                game_subject = input(f"{BLUE}> {RESET}").strip()
        else:
            # Ask user for game project idea
            print(f"{BLUE}What type of Unity game would you like to create?{RESET}")
            print(f"{BLUE}Please describe your game idea (e.g., 'A 2D platformer with time-travel mechanics'):{RESET}")
            game_subject = input(f"{BLUE}> {RESET}").strip()
        
        if not game_subject:
            print(f"{YELLOW}No game idea provided. Using default example...{RESET}")
            game_subject = "A unity 2D PIXEL game for dyslexic children to help them learn the alphabet and numbers in a fun way"
            print(f"{YELLOW}Using: {game_subject}{RESET}")
        
        # Initialize the brainstorming agent    
        brainstorming_agent = Brainstorm.BrainstormingAgent()
        
        # Start brainstorming process
        print(f"{GREEN}Starting brainstorming process for: {game_subject}{RESET}")
        brainstorm_content = await brainstorming_agent.get_gemini_response(game_subject)
        
        # Update brainstorming results and generate UI suggestions
        await brainstorming_agent.update_brainstorming_results(brainstorm_content)
        
        # Iterative refinement loop
        refining_complete = False
        current_brainstorm = brainstorm_content
        
        while not refining_complete:
            # Ask user if they want to refine the brainstorming
            print(f"\n{BLUE}Brainstorming has finished. Do you want to change something? (yes/no){RESET}")
            refine_choice = input(f"{BLUE}> {RESET}").strip().lower()
            
            if refine_choice == "no":
                refining_complete = True
                continue
            elif refine_choice == "yes" or refine_choice:
                # Get user feedback for refinement
                print(f"{BLUE}Please provide your feedback or new ideas to incorporate:{RESET}")
                feedback = input(f"{BLUE}> {RESET}").strip()
                
                if feedback:
                    print(f"{GREEN}Updating brainstorming based on your feedback...{RESET}")
                    
                    # Update the brainstorming with user feedback
                    current_brainstorm = await brainstorming_agent.handle_feedback(feedback, current_brainstorm)
                    
                    print(f"{GREEN}Brainstorming updated successfully!{RESET}")
                    print(f"{GREEN}UI suggestions have been regenerated.{RESET}")
                else:
                    print(f"{YELLOW}No feedback provided. Continuing with current brainstorming.{RESET}")
            else:
                print(f"{YELLOW}Invalid input. Please answer 'yes' or 'no'.{RESET}")
        
        # Continue with main2's code generation process
        print(f"{GREEN}Proceeding to code generation based on the finalized brainstorming...{RESET}")
        await process.process_code_generation()
        
    elif choice == "2":
        print(f"{GREEN}Editing an existing Unity game...{RESET}")
        await process.process_existing_game_edits()
    else:
        print(f"{RED}Invalid choice. Please run the script again and enter 1 or 2.{RESET}")

if __name__ == "__main__":
    asyncio.run(main())