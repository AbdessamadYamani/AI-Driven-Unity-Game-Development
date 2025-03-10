from agent_base import DevelopmentAgent
import os
import platform
import subprocess
####################################### Brainstorming agent 

PURPLE = "\033[95m"
RESET = "\033[0m"

class BrainstormingAgent(DevelopmentAgent):
    
    def __init__(self):
        super().__init__("Brainstorming Agent", PURPLE)
        self.project_path = None
        
    async def get_gemini_response(self, game_subject):
        """Generate brainstorming ideas for the game concept"""
        prompt = fr"""
System Instruction:
You are a creative game design consultant with expertise in educational games and Unity development. Your task is to brainstorm compelling game concepts based on the provided subject.

User Instructions:
DO a brainstorming for the game subject: {game_subject}

Think about the following aspects:
1. Core gameplay mechanics
2. Visual style and art direction
3. Target audience and learning objectives
4. Key features that would make this game engaging
5. Potential challenges in development

Your brainstorming should focus on creating a game that is both educational and fun,
especially considering the available UI assets that will be used to create the game.

If there is previous brainstorming content included in the subject, build upon those ideas
with the new user feedback rather than starting from scratch.

Format your response as a comprehensive markdown document with clear sections and bullet points.
"""
        return await self.generate_initial(prompt)
    
    async def update_brainstorming_results(self, brainstorm_content):
        """Update the brainstorming results in the brainstorm.md file and trigger UI suggestion generation"""
        try:
            # Create a new brainstorm file
            with open("brainstorm.md", "w", encoding="utf-8") as file:
                file.write(f"# Game Brainstorming Results\n\n{brainstorm_content}")
            
            print(f"{self.color}Brainstorming results updated successfully.{RESET}")
            
            # Regenerate UI suggestions based on the updated brainstorming
            print(f"{self.color}Regenerating UI structure suggestions...{RESET}")
            
            # This would call the UI suggestion generator
            await self.generate_ui_suggestions(brainstorm_content)
            
            return "Brainstorming results updated and UI suggestions regenerated successfully."
        except Exception as e:
            error_msg = f"Error updating brainstorming results: {str(e)}"
            print(f"{self.color}{error_msg}{RESET}")
            return error_msg
    
    def select_project_path(self):
        """Ask user for Unity project path instead of using hardcoded value"""
        if self.project_path:
            # If we already have a path, ask if user wants to use it again
            print(f"{self.color}Current Unity project path: {self.project_path}{RESET}")
            reuse = input(f"{self.color}Would you like to use this path? (yes/no): {RESET}").strip().lower()
            if reuse == "yes":
                return self.project_path
        
        # Ask user for project path
        print(f"{self.color}Please provide the path to your Unity project folder:{RESET}")
        print(f"{self.color}(e.g., C:\\Users\\username\\MyUnityProject or /Users/username/MyUnityProject){RESET}")
        
        # Option to use file dialog
        use_dialog = input(f"{self.color}Would you like to use a file dialog to select the folder? (yes/no): {RESET}").strip().lower()
        
        if use_dialog == "yes":
            path = self._open_folder_dialog()
            if path:
                self.project_path = path
                return path
        
        # Manual input if dialog fails or user prefers typing
        path = input(f"{self.color}Project path > {RESET}").strip()
        
        # Validate path
        if not os.path.isdir(path):
            print(f"{self.color}Warning: The provided path doesn't exist or is not a directory.{RESET}")
            create = input(f"{self.color}Would you like to create this directory? (yes/no): {RESET}").strip().lower()
            if create == "yes":
                try:
                    os.makedirs(path, exist_ok=True)
                    print(f"{self.color}Directory created successfully.{RESET}")
                except Exception as e:
                    print(f"{self.color}Error creating directory: {str(e)}{RESET}")
                    return None
            else:
                return None
        
        self.project_path = path
        return path
    
    def _open_folder_dialog(self):
        """Open a folder selection dialog that works across platforms"""
        folder_path = None
        
        try:
            if platform.system() == "Windows":
                # PowerShell approach for Windows
                powershell_cmd = """
                Add-Type -AssemblyName System.Windows.Forms
                $folderDialog = New-Object System.Windows.Forms.FolderBrowserDialog
                $folderDialog.Description = "Select Unity Project Folder"
                $folderDialog.ShowDialog() | Out-Null
                $folderDialog.SelectedPath
                """
                result = subprocess.run(["powershell", "-Command", powershell_cmd], capture_output=True, text=True)
                folder_path = result.stdout.strip()
            elif platform.system() == "Darwin":  # macOS
                # AppleScript for macOS
                script = """
                osascript -e 'tell application "System Events"
                    activate
                    set folderPath to choose folder with prompt "Select Unity Project Folder"
                    POSIX path of folderPath
                end tell'
                """
                result = subprocess.run(script, shell=True, capture_output=True, text=True)
                folder_path = result.stdout.strip()
            else:  # Linux and others
                # Try using zenity if available
                try:
                    result = subprocess.run(
                        ["zenity", "--file-selection", "--directory", "--title=Select Unity Project Folder"], 
                        capture_output=True, 
                        text=True
                    )
                    folder_path = result.stdout.strip()
                except FileNotFoundError:
                    print(f"{self.color}Could not find a graphical folder dialog tool. Please provide the folder path manually.{RESET}")
                    return None
        except Exception as e:
            print(f"{self.color}Error opening folder dialog: {str(e)}{RESET}")
            return None
        
        # Check if a folder was actually selected
        if not folder_path or not os.path.isdir(folder_path):
            return None
            
        return folder_path
    
    def find_resources_folder(self, base_path):
        """Find the Resources/UIs folder in the Unity project structure"""
        # Common paths to check
        potential_paths = [
            os.path.join(base_path, "Assets", "Resources", "UIs"),
            os.path.join(base_path, "Assets", "Resources", "UI"),
            os.path.join(base_path, "Assets", "Resources")
        ]
        
        # Check if any of the common paths exist
        for path in potential_paths:
            if os.path.isdir(path):
                return path
        
        # If not found, search for Resources folder
        assets_path = os.path.join(base_path, "Assets")
        if os.path.isdir(assets_path):
            for root, dirs, files in os.walk(assets_path):
                if "Resources" in dirs:
                    resources_path = os.path.join(root, "Resources")
                    # Look for UI or UIs folder inside Resources
                    if "UIs" in os.listdir(resources_path):
                        return os.path.join(resources_path, "UIs")
                    elif "UI" in os.listdir(resources_path):
                        return os.path.join(resources_path, "UI")
                    else:
                        return resources_path
        
        # If still not found, ask user to specify
        print(f"{self.color}Could not automatically find Resources folder.{RESET}")
        print(f"{self.color}Please specify the path to your UI assets folder relative to the project root:{RESET}")
        print(f"{self.color}(e.g., Assets/Resources/UIs){RESET}")
        rel_path = input(f"{self.color}> {RESET}").strip()
        full_path = os.path.join(base_path, *rel_path.replace('\\', '/').split('/'))
        
        if not os.path.isdir(full_path):
            print(f"{self.color}Warning: The specified path doesn't exist.{RESET}")
            create = input(f"{self.color}Would you like to create this directory? (yes/no): {RESET}").strip().lower()
            if create == "yes":
                try:
                    os.makedirs(full_path, exist_ok=True)
                    print(f"{self.color}Directory created successfully.{RESET}")
                    return full_path
                except Exception as e:
                    print(f"{self.color}Error creating directory: {str(e)}{RESET}")
                    return None
            return None
        
        return full_path
    
    def get_directory_structure(self, resources_path):
        """
        Traverses the UI assets directory and creates a text representation of its structure.
        
        Args:
            resources_path (str): Path to the resources folder
            
        Returns:
            str: A string representing the directory structure
        """
        structure = f"UI Assets Structure (from {resources_path}):\n"
        
        if not os.path.isdir(resources_path):
            return f"{structure}Directory not found."
        
        def traverse_directory(directory, indent=""):
            nonlocal structure
            try:
                items = os.listdir(directory)
                for item in sorted(items):
                    item_path = os.path.join(directory, item)
                    if os.path.isdir(item_path):
                        # Add folder to the structure
                        structure += f"{indent}|----->{item}\\\n"
                        # Recurse into subdirectory
                        traverse_directory(item_path, indent + "      ")
                    elif os.path.isfile(item_path) and item.lower().endswith((".png", ".jpg", ".jpeg", ".svg")):
                        # Add image file to the structure
                        structure += f"{indent}|------>{item}\n"
            except Exception as e:
                structure += f"{indent}|----->Error accessing directory: {str(e)}\n"
        
        traverse_directory(resources_path)
        return structure
    
    async def generate_ui_suggestions(self, brainstorm_content):
        """Generate UI structure suggestions based on brainstorming content and available UI assets"""
        # Get the project path from the user
        project_path = self.select_project_path()
        if not project_path:
            print(f"{self.color}No valid project path provided. Using generic UI suggestions.{RESET}")
            ui_assets_info = "No UI assets information available."
        else:
            # Find the Resources/UIs folder
            resources_path = self.find_resources_folder(project_path)
            if resources_path:
                print(f"{self.color}Found resources folder: {resources_path}{RESET}")
                # Get the directory structure
                ui_assets_info = self.get_directory_structure(resources_path)
                print(f"{self.color}Successfully analyzed UI assets.{RESET}")
            else:
                print(f"{self.color}Could not locate UI assets. Using generic UI suggestions.{RESET}")
                ui_assets_info = "No UI assets information available."
        
        # Show the UI assets to the user
        print(f"{self.color}\nUI Assets Analysis:\n{ui_assets_info}{RESET}")
        
        # Generate UI suggestions based on brainstorming and available assets
        prompt = fr"""
System Instruction:
You are a UI/UX expert specializing in Unity game development. Based on the provided game brainstorming and available UI assets, suggest appropriate UI elements and structure.

User Instructions:
Analyze this game brainstorming content and suggest UI elements:

{brainstorm_content}

Available UI Assets:
{ui_assets_info}

Based on both the game concept and available assets, provide recommendations for:
1. Main menu layout and elements
2. In-game UI components
3. Navigation structure
4. Visual style guidelines for UI
5. Necessary screens (settings, level select, etc.)
6. How to best utilize the available UI assets to acheive the brainstorming goal.
7. Your report should not have the assets structure.

If specific assets are mentioned, reference them directly in your suggestions.
"""
        ui_suggestions = await self.generate_initial(prompt)
        
        # Save UI suggestions to a file
        with open("ui_suggestions.md", "w", encoding="utf-8") as file:
            file.write(f"# UI Structure Suggestions\n\n## Based on Available UI Assets\n\n{ui_assets_info}\n\n## Suggestions\n\n{ui_suggestions}")
        
        print(f"{self.color}UI suggestions generated and saved successfully.{RESET}")
        return ui_suggestions
    
    async def handle_feedback(self, feedback, current_brainstorm):
        """Process feedback on the brainstorming and update the ideas accordingly"""
        prompt = f"""
You are the Brainstorming Agent responsible for game concept development.

The user has provided feedback on your brainstorming:

{feedback}

Your current brainstorming:
{current_brainstorm}

Refine and improve the game concept based on this feedback. Incorporate the suggestions
while maintaining the strengths of the original concept. If the feedback contradicts
previous directions, prioritize the new feedback.

Format your response as a comprehensive markdown document with clear sections and bullet points.
"""
        
        print(f"{self.color}Brainstorming Agent processing feedback...{RESET}")
        updated_brainstorm = await self.generate_initial(prompt)
        
        # Update the brainstorming file with the new content
        await self.update_brainstorming_results(updated_brainstorm)
        
        print(f"{self.color}=== Brainstorming Update Complete ===")
        print(f"{self.color}Brainstorming has been refined based on feedback.{RESET}")
        print(f"{self.color}================================={RESET}")
        
        return updated_brainstorm