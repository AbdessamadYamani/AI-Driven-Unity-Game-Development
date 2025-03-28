import os
import re
import sys
import json
import time
import asyncio
import threading
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox
import google.generativeai as genai
from typing import List, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import mammoth  # For .docx file handling

# Import the scene analysis function
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from watchdog_tool import comprehensive_scene_analysis

# Color codes
GREEN = "\033[92m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"

def select_project_path() -> str:
    """
    Open a file dialog for selecting Unity project directory
    
    Returns:
        str: Selected project path
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    project_path = filedialog.askdirectory(
        title="Select Unity Project Directory",
        initialdir=os.path.expanduser("~")
    )
    
    return project_path

def select_gdd_file() -> str:
    """
    Open a file dialog for selecting Game Design Document
    
    Returns:
        str: Selected GDD file path
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    gdd_file = filedialog.askopenfilename(
        title="Select Game Design Document",
        initialdir=os.path.expanduser("~"),
        filetypes=[
            ("Word Documents", "*.docx"),
            ("PDF Files", "*.pdf"),
            ("Text Files", "*.txt"),
            ("All Files", "*.*")
        ]
    )
    
    return gdd_file

def extract_gdd_content(gdd_path: str) -> str:
    """
    Extract text content from GDD file
    
    Args:
        gdd_path (str): Path to the GDD file
    
    Returns:
        str: Extracted text content from the document
    """
    try:
        # Handle .docx files using mammoth
        if gdd_path.lower().endswith('.docx'):
            with open(gdd_path, "rb") as docx_file:
                result = mammoth.extract_raw_text(docx_file)
                return result.value
        
        # Handle txt files
        elif gdd_path.lower().endswith('.txt'):
            with open(gdd_path, 'r', encoding='utf-8') as txt_file:
                return txt_file.read()
        
        # Handle PDF (requires additional library)
        elif gdd_path.lower().endswith('.pdf'):
            try:
                import PyPDF2
                with open(gdd_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    return ' '.join(page.extract_text() for page in pdf_reader.pages)
            except ImportError:
                print(f"{RED}PyPDF2 library not installed. Cannot read PDF.{RESET}")
                return ""
        
        else:
            print(f"{RED}Unsupported file format: {gdd_path}{RESET}")
            return ""
    
    except Exception as e:
        print(f"{RED}Error extracting GDD content: {e}{RESET}")
        print(f"{BLUE}Traceback:{RESET}")
        import traceback
        traceback.print_exc()
        return ""



class UnityLearningTutor:
    def __init__(self, gemini_api_key: str, project_path: str, gdd_content: str):
        # Initialize Gemini AI
        genai.configure(api_key=gemini_api_key)
        self.gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Project and learning path attributes
        self.project_path = project_path
        self.learning_path = {}
        self.current_chapter_index = 0
        self.current_task_index = 0
        self.gdd_content = gdd_content
        
        # Progress tracking
        self.progress_file = os.path.join(project_path, 'dyslexia_game_progress.json')
        
        # Thread-safe scene change flag
        self._scene_change_flag = threading.Event()
        
        # Watchdog setup
        self.watchdog = None
        self.watchdog_observer = None
        
        # Scene analysis tracking
        self.scene_analysis_count = 0
        
        # Load existing progress
        self.load_progress()

    def extract_json(response: str) -> Dict:
        """
        Reliably extract JSON from a text response
        
        Args:
            response (str): Text potentially containing JSON
        
        Returns:
            Dict: Extracted JSON object
        """
        # First try a simple JSON extraction using regex
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if json_match:
            try:
                # Try parsing the matched text as JSON
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                # If simple parsing fails, try more robust parsing
                try:
                    # Use a more sophisticated JSON extraction
                    import jsonlines
                    from io import StringIO
                    
                    # Create a string buffer
                    json_buffer = StringIO(response)
                    
                    # Try to read JSON using jsonlines
                    for item in jsonlines.Reader(json_buffer):
                        return item
                except:
                    # Fallback to manual JSON parsing
                    print(f"{RED}Could not extract valid JSON from response{RESET}")
                    print(f"{BLUE}Raw Response:{RESET}\n{response}")
                    raise ValueError("Unable to extract JSON")
        
        raise ValueError("No JSON found in the response")

    def save_progress(self):
        """
        Save current learning progress to a JSON file, including the full learning path
        """
        progress_data = {
            'learning_path': self.learning_path,  # Save the entire learning path
            'current_chapter_index': self.current_chapter_index,
            'current_task_index': self.current_task_index
        }
        
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=4)
            print(f"{GREEN}Progress saved successfully!{RESET}")
        except Exception as e:
            print(f"{RED}Error saving progress: {e}{RESET}")

    def choose_start_mode(self):
        """
        Provide user with options to start or continue learning
        """
        while True:
            print("\n--- Unity Learning Tutor ---")
            print("1. Start a New Learning Path")
            print("2. Continue Previous Progress")
            print("3. Exit")
            
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == '1':
                # Generate new learning path
                return 'new'
            elif choice == '2':
                # Check for existing progress
                progress = self.load_progress()
                if progress:
                    # Display progress details
                    chapter = progress['current_chapter_index'] + 1
                    task = progress['current_task_index'] + 1
                    
                    print(f"\n{CYAN}Previous Progress Found:{RESET}")
                    print(f"Currently at Chapter {chapter}, Task {task}")
                    
                    continue_choice = input("Do you want to continue from here? (yes/no): ").lower().strip()
                    if continue_choice in ['yes', 'y']:
                        # Load the existing progress
                        self.learning_path = progress['learning_path']
                        self.current_chapter_index = progress['current_chapter_index']
                        self.current_task_index = progress['current_task_index']
                        return 'continue'
                else:
                    print(f"{RED}No valid progress found. Starting a new learning path.{RESET}")
                    return 'new'
            elif choice == '3':
                # Exit the application
                sys.exit(0)
            else:
                print(f"{RED}Invalid choice. Please try again.{RESET}")

    def load_progress(self):
        """
        Load existing progress from JSON file
        Returns a dictionary with progress details or None if no progress exists
        """
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    progress_data = json.load(f)
                
                # Verify the progress data has all required keys
                if all(key in progress_data for key in ['learning_path', 'current_chapter_index', 'current_task_index']):
                    return progress_data
                else:
                    print(f"{RED}Incomplete progress data found.{RESET}")
                    return None
            except Exception as e:
                print(f"{RED}Error loading progress: {e}{RESET}")
                return None
        return None

    def get_directory_structure(self, project_path: str = None) -> Dict[str, Any]:
        """
        Traverses the UI assets directory and creates a comprehensive structure 
        of available UI sprites.
        
        Args:
            project_path (str): Base path of the Unity project, defaults to self.project_path
        
        Returns:
            Dict containing directory structure and sprite details
        """
        # Use self.project_path if no path is provided
        if project_path is None:
            project_path = self.project_path
        
        # Potential UI resources paths
        ui_resource_paths = [
            os.path.join(project_path, 'Assets', 'Resources', 'UIs'),
            os.path.join(project_path, 'Assets', 'UI', 'Sprites'),
            os.path.join(project_path, 'Assets', 'Sprites', 'UI')
        ]
        
        # Resulting structure
        ui_structure = {
            'directory_text': "",
            'sprites': []
        }
        
        def traverse_directory(directory: str, indent: str = "") -> None:
            """
            Recursively traverse directory and build structure
            """
            try:
                # Check if directory exists
                if not os.path.exists(directory):
                    return
                
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    
                    if os.path.isdir(item_path):
                        # Add folder to the structure
                        ui_structure['directory_text'] += f"{indent}|----->{item}\\\n"
                        # Recurse into subdirectory
                        traverse_directory(item_path, indent + "      ")
                    
                    elif os.path.isfile(item_path):
                        # Check for image file extensions
                        if item.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.sprite')):
                            # Add image file to structure and sprites list
                            ui_structure['directory_text'] += f"{indent}|------>{item}\n"
                            
                            # Collect sprite details
                            sprite_info = {
                                'filename': item,
                                'full_path': item_path,
                                'relative_path': os.path.relpath(item_path, project_path)
                            }
                            ui_structure['sprites'].append(sprite_info)
            
            except Exception as e:
                print(f"{RED}Error traversing directory {directory}: {e}{RESET}")
        
        # Try each potential UI resources path
        for potential_path in ui_resource_paths:
            if os.path.exists(potential_path):
                traverse_directory(potential_path)
                break
        
        return ui_structure

    def prepare_sprite_details_for_gemini(self, sprite_structure: Dict[str, Any]) -> str:
        """
        Prepare sprite details in a format suitable for Gemini AI prompt
        
        Args:
            sprite_structure (Dict): Sprite directory structure
        
        Returns:
            str: Formatted sprite details
        """
        # If no sprites found
        if not sprite_structure['sprites']:
            return "No UI sprites found in the project."
        
        # Prepare detailed sprite information
        sprite_details = "Available UI Sprites:\n"
        sprite_details += "-------------------\n"
        
        for sprite in sprite_structure['sprites']:
            sprite_details += f"- Filename: {sprite['filename']}\n"
            sprite_details += f"  Relative Path: {sprite['relative_path']}\n"
        
        # Add directory structure
        sprite_details += "\nDirectory Structure:\n"
        sprite_details += sprite_structure['directory_text']
        
        return sprite_details

    async def generate_learning_path(self) -> Dict:
        """
        Generate a comprehensive learning path for the Dyslexia Support Game
        Enhanced with available UI sprite information and GDD insights
        """
        # Get UI sprite structure
        sprite_structure = self.get_directory_structure()
        sprite_details = self.prepare_sprite_details_for_gemini(sprite_structure)
        
        game_concept = f"""
        Game Concept for Dyslexia Support Educational Game
        
        Game Design Document Insights:
        {self.gdd_content[:1000]}  # Limit to first 1000 characters to prevent overwhelming the prompt
        
        Target Audience: Children with dyslexia
        Purpose: Address challenges in vowel and consonant recognition, sound blending, and word formation

        Game Worlds:
        1. Vowel Island: Vowel recognition and pronunciation
        2. Consonant Island: Consonant recognition and usage
        3. Blend Island: Blending consonants and diphthongs
        4. Word Island: Blending and forming words

        Objective: Create an interactive, educational game that supports children with dyslexia in language learning
        """
        
        prompt = f"""
        Create a comprehensive JSON learning path for Unity game development, focusing on creating an educational game for children with dyslexia.

        Game Concept Details:
        {game_concept}

        Available UI Sprites:
        {sprite_details}

        Learning Path Requirements:
        1. 4 progressive chapters
        2. Each chapter focuses on creating a specific game island
        3. Tasks involve creating game objects, UI, and interactive elements
        4. Final task of each chapter: Create the island's main scene
        5. Ensure hands-on, practical learning for game development
        6. Utilize available UI sprites in game design
        7. Recommend specific sprite usage for each island
        8. Give only the json answer, no explanations or intros, only the json answer.

        JSON Structure Requirements:
        - Include sprite recommendations for UI elements
        - Create tasks that leverage existing sprites
        - Ensure each chapter has multiple tasks
        - Design tasks with clear, step-by-step instructions
        - Include expected object details for each task

        Sprites Context:
        - If specific sprites are available, design tasks around their usage
        - Create UI elements that match available sprite types
        - Suggest creative ways to use existing sprites in dyslexia learning game

        Example JSON Output:
        {{
            "chapters": [
                {{
                    "number": 1,
                    "title": "Vowel Island Setup",
                    "tasks": [
                        {{
                            "number": 1,
                            "description": "Create Vowel Island Main Camera",
                            "explanation": "Set up the primary camera for Vowel Island to define the player's view",
                            "recommended_sprites": [
                                "background_sprite.png",
                                "camera_frame.png"
                            ],
                            "expected_object": {{
                                "type": "Camera",
                                "name": "VowelIslandCamera",
                                "components": ["Camera", "Transform"]
                            }},
                            "steps": [
                                "Open Hierarchy Window",
                                "Right-Click > 2D Object > Camera",
                                "Rename camera to 'VowelIslandCamera'",
                                "Position camera to capture entire Vowel Island scene"
                            ]
                        }}
                    ]
                }}
            ]
        }}
        """
        
        try:
            response = await self.generate_initial(prompt)
            
            # Robust JSON extraction function
            def extract_json(text: str) -> Dict:
                # First, try to extract JSON using regex
                json_match = re.search(r'\{.*\}', text, re.DOTALL | re.MULTILINE)
                
                if json_match:
                    try:
                        # Attempt to parse the JSON
                        learning_path = json.loads(json_match.group(0))
                        return learning_path
                    except json.JSONDecodeError:
                        # If direct parsing fails, try more aggressive cleaning
                        try:
                            # Remove any text before the first '{' and after the last '}'
                            cleaned_text = text[text.index('{'):text.rindex('}')+1]
                            return json.loads(cleaned_text)
                        except (ValueError, json.JSONDecodeError):
                            print(f"{RED}JSON Parsing Error: Unable to extract valid JSON{RESET}")
                            print(f"{BLUE}Raw Response:{RESET}\n{response}")
                            raise ValueError("Invalid JSON structure")
                
                raise ValueError("No valid JSON found in the response")
            
            # Extract and return the learning path
            learning_path = extract_json(response)
            return learning_path
        
        except Exception as e:
            print(f"{RED}Error generating learning path: {e}{RESET}")
            traceback.print_exc()
            raise

    async def generate_initial(self, prompt: str) -> str:
        """
        Generate initial response using Gemini AI
        """
        try:
            response = await asyncio.to_thread(
                self.gemini_client.generate_content, 
                prompt
            )
            return response.text
        except Exception as e:
            print(f"{RED}Gemini AI Error: {e}{RESET}")
            raise

    async def validate_task_completion(self, current_task: Dict) -> bool:
        """
        Validate task completion using scene analysis and Gemini AI
        First check if task objects already exist
        """
        # Perform scene analysis
        scene_analysis = comprehensive_scene_analysis(self.project_path)
        self.scene_analysis_count += 1
        
        # Prepare validation prompt to check for pre-existing tasks
        validation_prompt = f"""
    Context: You are a Unity game development expert reviewing a pre-existing scene.

    Scene Analysis:
    {json.dumps(scene_analysis, indent=2)}

    Task Details:
    {json.dumps(current_task, indent=2)}

    Validation Instructions:
    1. Carefully review the scene analysis
    2. Check if the expected object for this task already exists in the scene
    3. If the object exists, respond with 'pre-existing'
    4. If the object does not exist, respond with 'not-created'
    5. Look for exact name and type matching the task's expected object

    ANSWER WITH ONLY ONE WORD with 0 explanation - just one word
    Evaluation Question: Are the task's expected objects already present in the scene?
    """
        
        try:
            # Get Gemini validation
            validation_response = await self.generate_initial(validation_prompt)
            
            # Extract validation result
            match = re.search(r'\b(pre-existing|not-created)\b', validation_response.lower())
            
            if match and match.group(1) == 'pre-existing':
                # Task objects already exist
                print(f"{GREEN}✓ You have already created: {current_task['description']}{RESET}")
                
                # Automatically mark as completed and save progress
                self.save_progress()
                return True
            
            # Wait for scene change signal if not pre-existing
            print(f"{CYAN}Waiting for scene change... (Press Ctrl+C to cancel){RESET}")
            try:
                # Wait for either the event or a timeout
                await asyncio.wait_for(self.wait_for_scene_change(), timeout=600)  # 10-minute timeout
            except asyncio.TimeoutError:
                print(f"{RED}Task completion timeout. Please complete the task.{RESET}")
                return False
            
            # Perform standard validation for newly created objects
            validation_prompt = f"""
    Context: You are a Unity game development expert validating a task completion for a dyslexia support game.

    Scene Analysis:
    {json.dumps(scene_analysis, indent=2)}

    Task Details:
    {json.dumps(current_task, indent=2)}

    Validation Instructions:
    1. Carefully review the scene analysis
    2. Compare the scene with the task's requirements
    3. Respond with a precise 'yes' or 'no'
    4. If 'no', provide a brief explanation of what's missing
    Note: if you spot the object was created like what the task asks for, say yes

    ANSWER WITH ONLY ONE WORD with 0 explanation - just one word
    Evaluation Question: Has the user successfully created the specified object exactly as required?
    """
            
            # Get Gemini validation
            validation_response = await self.generate_initial(validation_prompt)
            
            # Print Gemini's detailed response
            print(f"\n{BLUE}Validation Result:{RESET}")
            print(validation_response)
            
            # Extract yes/no response using regex
            match = re.search(r'\b(yes|no)\b', validation_response.lower())
            
            task_completed = match.group(1) == 'yes' if match else False
            
            # Save progress if task is completed
            if task_completed:
                self.save_progress()
            
            return task_completed
        
        except Exception as e:
            print(f"{RED}Task validation error: {e}{RESET}")
            return False

    async def wait_for_scene_change(self):
        """
        Wait for scene change using thread-safe event
        """
        while not self._scene_change_flag.is_set():
            await asyncio.sleep(0.5)
        
        # Reset the flag for next use
        self._scene_change_flag.clear()

    async def present_current_task(self) -> bool:
        """
        Present the current task to the user
        """
        if not self.learning_path or self.current_chapter_index >= len(self.learning_path['chapters']):
            print(f"{GREEN}Congratulations! You've completed the Dyslexia Support Game development tutorial.{RESET}")
            return False
        
        current_chapter = self.learning_path['chapters'][self.current_chapter_index]
        
        if self.current_task_index >= len(current_chapter['tasks']):
            self.current_chapter_index += 1
            self.current_task_index = 0
            return await self.present_current_task()
        
        current_task = current_chapter['tasks'][self.current_task_index]
        
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Display task information
        print(f"{BLUE}Chapter {current_chapter['number']}: {current_chapter.get('title', 'Unnamed Chapter')}{RESET}")
        print(f"{CYAN}Task {current_task['number']}: {current_task['description']}{RESET}")
        
        # Display task explanation
        print(f"\n{GREEN}Task Explanation:{RESET}")
        print(current_task.get('explanation', 'No additional explanation provided.'))
        
        # Display task steps
        print(f"\n{BLUE}Creation Steps:{RESET}")
        for step in current_task.get('steps', []):
            print(f"• {step}")
        
        print(f"\n{CYAN}I'm waiting for you to complete the task: {current_task['description']} ...{RESET}")
        print(f"{GREEN}Instructions: Save your Unity scene after completing the task.{RESET}")
        
        # Reset scene change flag
        self._scene_change_flag.clear()
        
        return True

    async def run_learning_path(self):
        """
        Main execution method for learning path
        """
        try:
            # Choose start mode
            start_mode = self.choose_start_mode()
            
            # Generate learning path if in new mode or no existing path
            if start_mode == 'new' or not self.learning_path:
                self.learning_path = await self.generate_learning_path()
                # Reset progress
                self.current_chapter_index = 0
                self.current_task_index = 0
            
            # Setup watchdog for project monitoring
            self.setup_watchdog()
            
            # Main learning loop
            while await self.present_current_task():
                # Validate task completion
                current_task = self.learning_path['chapters'][self.current_chapter_index]['tasks'][self.current_task_index]
                task_completed = await self.validate_task_completion(current_task)
                
                if task_completed:
                    print(f"{GREEN}Task completed successfully!{RESET}")
                    print(f"{CYAN}Scene analysis performed {self.scene_analysis_count} times.{RESET}")
                    self.current_task_index += 1
                    
                    # Save progress after each task
                    self.save_progress()
                
                # Add a small delay to prevent rapid cycling
                await asyncio.sleep(2)
        
        except Exception as e:
            print(f"{RED}Learning path execution error: {e}{RESET}")
            traceback.print_exc()
        finally:
            self.cleanup_watchdog()

    def setup_watchdog(self):
        """
        Setup file system watchdog for project monitoring
        """
        class ProjectWatchdog(FileSystemEventHandler):
            def __init__(self, learning_tutor):
                self.learning_tutor = learning_tutor
                self.last_analyzed_time = 0
            
            def on_modified(self, event):
                # Only react to Unity scene files
                if not event.is_directory and event.src_path.endswith('.unity'):
                    current_time = time.time()
                    if current_time - self.last_analyzed_time > 2:  # 2-second cooldown
                        self.last_analyzed_time = current_time
                        print(f"{GREEN}Scene saved! Processing changes...{RESET}")
                        # Set the thread-safe scene change flag
                        self.learning_tutor._scene_change_flag.set()
        
        self.watchdog = ProjectWatchdog(self)
        self.watchdog_observer = Observer()
        self.watchdog_observer.schedule(self.watchdog, self.project_path, recursive=True)
        self.watchdog_observer.start()

    def cleanup_watchdog(self):
        """
        Cleanup watchdog resources
        """
        if self.watchdog_observer:
            self.watchdog_observer.stop()
            self.watchdog_observer.join()

async def main():
    # Select project path via file dialog
    project_path = select_project_path()
    
    # Select GDD file via file dialog
    gdd_path = select_gdd_file()
    
    # Extract GDD content
    gdd_content = extract_gdd_content(gdd_path)
    
    # Get Gemini API key
    gemini_api_key = input("Enter your Gemini API Key: ").strip()
    
    # Initialize and run learning tutor
    tutor = UnityLearningTutor(gemini_api_key, project_path, gdd_content)
    await tutor.run_learning_path()

if __name__ == "__main__":
    asyncio.run(main())