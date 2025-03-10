import os
import re
import asyncio
import json
import datetime
import tkinter as tk
from tkinter import filedialog
from typing import Dict, Optional, List
from Agents.tester import GameDevTester  
from Agents.Game_Manager import GameManagerAgent
from Agents.Game_Controller import GameControllerAgent
from Agents.Game_UI import GameUIAgent
from Agents.Scenes import ScenesAgent
from Agents.unity_code_editor import UnityCodeEditorAgent  

GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"


def browse_directory() -> str:
    """
    Opens a file browser dialog to select a directory.
    
    Returns:
        The selected directory path or empty string if canceled.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.attributes('-topmost', True)  # Bring dialog to front
    directory = filedialog.askdirectory(title="Select Directory")
    root.destroy()
    return directory


def browse_unity_project() -> str:
    """
    Opens a file browser dialog to select a Unity project directory.
    Verifies that the selected directory has Unity project structure.
    
    Returns:
        The selected Unity project path or empty string if canceled or invalid.
    """
    while True:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring dialog to front
        directory = filedialog.askdirectory(title="Select Unity Project Folder")
        root.destroy()
        
        if not directory:  # User canceled
            return ""
            
        # Verify it looks like a Unity project
        if os.path.exists(os.path.join(directory, "Assets")) and os.path.exists(os.path.join(directory, "ProjectSettings")):
            return directory
        else:
            print(f"{YELLOW}Warning: The selected folder doesn't appear to be a valid Unity project.{RESET}")
            retry = input(f"{YELLOW}Try again? (y/n): {RESET}").strip().lower()
            if retry != 'y':
                print(f"{YELLOW}Using selected directory anyway: {directory}{RESET}")
                return directory


def extract_and_place_files(markdown_file_path: str, base_project_path: str) -> bool:
    """
    Extracts file sections from a markdown file and writes them to their
    corresponding locations in the Unity project.

    Each file section should be enclosed between:
      ### FILE START: <filepath>
      ... file contents ...
      ### FILE END

    Args:
        markdown_file_path: Path to the markdown file.
        base_project_path: Base path of the Unity project.

    Returns:
        True if the files were successfully extracted and written; False otherwise.
    """
    try:
        with open(markdown_file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Regex to capture file paths and their corresponding content
        file_pattern = r'### FILE START: (.+?)\n(.*?)### FILE END'
        file_matches = re.findall(file_pattern, content, re.DOTALL)

        if not file_matches:
            print(f"{RED}No file sections found in {markdown_file_path}{RESET}")
            return False

        for file_path, file_content in file_matches:
            cleaned_content = file_content.strip()
            # Build full path (handle relative vs. absolute paths)
            full_file_path = (
                os.path.join(base_project_path, file_path.strip())
                if not file_path.startswith(base_project_path)
                else file_path.strip()
            )
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
            with open(full_file_path, 'w', encoding='utf-8') as out_file:
                out_file.write(cleaned_content)
            print(f"{GREEN}Created file: {full_file_path}{RESET}")

        return True
    except Exception as e:
        print(f"{RED}Error in extract_and_place_files: {e}{RESET}")
        return False


async def generate_all_scripts() -> Dict[str, str]:
    """
    Generates all scripts by calling each agent's generation method.

    Returns:
        A dictionary mapping each agent name to its generated script.
    """
    agents = {
        'Game_Manager': (GameManagerAgent(), BLUE),
        'Game_Controller': (GameControllerAgent(), BLUE),
        'Game_UI': (GameUIAgent(), BLUE),
        'Scenes': (ScenesAgent(), BLUE),
    }

    scripts: Dict[str, str] = {}
    for agent_name, (agent, color) in agents.items():
        print(f"{color}Generating {agent_name} script...{RESET}")
        scripts[agent_name] = await agent.get_gemini_response()
    return scripts


async def integration_loop() -> Dict[str, str]:
    """
    Iteratively integrates and refines scripts until compatibility is achieved or
    the maximum number of iterations is reached.

    Returns:
        A dictionary mapping each agent name to its final script.
    """
    agent_scripts = await generate_all_scripts()
    iteration = 0
    max_iterations = 3

    tester = GameDevTester()
    tester.scripts = {f"{name}.md": script for name, script in agent_scripts.items()}

    # Prepare agents for feedback processing
    agents = {
        'Game_Manager': (GameManagerAgent(), BLUE),
        'Game_Controller': (GameControllerAgent(), BLUE),
        'Game_UI': (GameUIAgent(), BLUE),
        'Scenes': (ScenesAgent(), BLUE),
    }

    while iteration < max_iterations:
        iteration += 1
        print(f"\n{GREEN}===== Integration Iteration {iteration} ====={RESET}")

        tester_feedback = await tester.analyze_integration()
        print(f"\n{GREEN}Tester Report:{RESET}\n{tester_feedback['report']}")

        if tester_feedback['status'].upper() == "DONE" and iteration >= 3:
            print(f"{GREEN}All scripts compatible after {iteration} iterations!{RESET}")
            return agent_scripts

        updated_scripts = agent_scripts.copy()
        for filename, feedback in tester_feedback.get('feedback', {}).items():
            if feedback.strip():
                agent_tuple = agents.get(filename)
                if agent_tuple:
                    agent_obj, _ = agent_tuple
                    current_script = tester.scripts.get(filename, "")
                    print(f"{GREEN}\nTester engaging {agent_obj.agent_name}{RESET}")
                    updated_code = await agent_obj.handle_feedback(feedback, current_script)
                    updated_scripts[filename.replace('.md', '')] = updated_code
                    tester.scripts[filename] = updated_code
                else:
                    print(f"{RED}No agent found for {filename}. Available agents: {list(agents.keys())}{RESET}")

        agent_scripts = updated_scripts
        print(f"{GREEN}\nRe-evaluating updated scripts...{RESET}")

    print(f"{GREEN}Max iterations ({max_iterations}) reached{RESET}")
    return agent_scripts


async def process_code_generation() -> None:
    """
    Coordinates the full process for creating a new Unity game, which includes:
      1. Running the integration loop to generate/refine scripts.
      2. Saving scripts as markdown files.
      3. Extracting files to the Unity project.
      4. Processing Unity compiler errors via user and historical feedback.
    """
    try:
        # Ask user to select Unity project directory
        print(f"{GREEN}Please select your Unity project directory in the file browser...{RESET}")
        project_path = browse_unity_project()
        if not project_path:
            print(f"{RED}No Unity project selected. Aborting.{RESET}")
            return
        print(f"{GREEN}Selected Unity project: {project_path}{RESET}")
            
        final_scripts = await integration_loop()
        if final_scripts is None:
            print(f"{RED}Integration failed.{RESET}")
            return

        # Save final scripts to markdown files.
        for agent, script in final_scripts.items():
            filename = f"{agent}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(script)
            print(f"{GREEN}Saved {filename}{RESET}")

        # Extract files into the Unity project.
        for agent in final_scripts.keys():
            extract_and_place_files(f"{agent}.md", project_path)
        print(f"{GREEN}All files extracted to Unity project{RESET}")

        tester = GameDevTester()

        # Load or create error history for Unity compiler errors.
        error_history_file = "unity_error_history.json"
        if os.path.exists(error_history_file):
            try:
                with open(error_history_file, 'r', encoding='utf-8') as f:
                    error_history = json.load(f)
                print(f"{GREEN}Loaded {len(error_history.get('errors', []))} previous errors from history{RESET}")
            except json.JSONDecodeError:
                error_history = {"errors": []}
                print(f"{YELLOW}Error history file was corrupted. Created new history.{RESET}")
        else:
            error_history = {"errors": []}
            print(f"{GREEN}Created new error history tracking file{RESET}")

        # Map Unity C# files to their corresponding agents.
        file_agent_mapping: Dict[str, str] = {}
        for agent, script in final_scripts.items():
            file_pattern = r'### FILE START: (.+?)\.cs'
            file_matches = re.findall(file_pattern, script, re.IGNORECASE)
            for file_path in file_matches:
                filename = os.path.basename(file_path)
                file_agent_mapping[filename + '.cs'] = agent
                print(f"{GREEN}Mapped {filename}.cs to {agent} agent{RESET}")

        async def process_error(error_message: str, is_historical: bool = False) -> bool:
            """
            Processes a single Unity compiler error by identifying the affected file,
            determining the responsible agent, and prompting a fix.

            Args:
                error_message: The Unity compiler error message.
                is_historical: True if the error comes from history; False for current errors.

            Returns:
                True if the error was successfully processed; False otherwise.
            """
            source_label = "Historical" if is_historical else "Current"
            print(f"\n{GREEN}==== Processing {source_label} Error ===={RESET}")
            print(f"{GREEN}Error message:{RESET}\n{error_message}")

            tester_prompt = f"""
You are a Game Developer Tester analyzing Unity compiler errors.
The user has reported the following issue:

{error_message}

Please analyze this error carefully to identify exactly which file needs to be fixed:
1. Extract the EXACT filename from the error (e.g., AutoSceneSetup.cs)
2. Identify the line number and error type
3. Determine what change is needed to fix the error

Provide structured feedback in this format:
UNITY_FILE: [the exact Unity C# file with error, e.g. AutoSceneSetup.cs]
LINE_NUMBER: [line number with error]
ERROR_TYPE: [brief description]
SOLUTION: [detailed solution explanation]
"""
            response = await asyncio.to_thread(lambda: tester.tester_chat.send_message(tester_prompt))
            analysis = response.text.strip()
            print(f"{GREEN}Tester Analysis:{RESET}\n{analysis}")

            unity_file_match = re.search(r'UNITY_FILE:\s*([\w\.]+\.cs)', analysis)
            if not unity_file_match:
                unity_file_match = re.search(r'Assets\\([\w\.]+\.cs)', error_message)
                if not unity_file_match:
                    print(f"{RED}Could not determine which Unity file is affected.{RESET}")
                    return False

            unity_file = unity_file_match.group(1)
            print(f"{GREEN}Found error in Unity file: {unity_file}{RESET}")

            responsible_agent: Optional[str] = None
            for cs_file, agent in file_agent_mapping.items():
                if cs_file.lower() == unity_file.lower():
                    responsible_agent = agent
                    break

            if not responsible_agent:
                print(f"{YELLOW}No direct mapping found for {unity_file}. Searching all MD files...{RESET}")
                for agent, script in final_scripts.items():
                    if unity_file in script:
                        responsible_agent = agent
                        print(f"{GREEN}Found {unity_file} in {agent}.md{RESET}")
                        break

            if not responsible_agent:
                search_prompt = f"""
Based on the Unity file {unity_file} that has an error, which agent would most likely be responsible for it:
1. Game_Manager - handles core game mechanics and state
2. Game_Controller - handles player input and controls
3. Game_UI - handles user interface elements
4. Scenes - handles level/scene setup and management
Analyze the filename and error to determine the most likely agent.
Respond with JUST ONE agent name from the list above.
"""
                response = await asyncio.to_thread(lambda: tester.tester_chat.send_message(search_prompt))
                responsible_agent = response.text.strip()

                if responsible_agent not in final_scripts:
                    if "manager" in responsible_agent.lower():
                        responsible_agent = "Game_Manager"
                    elif "control" in responsible_agent.lower():
                        responsible_agent = "Game_Controller"
                    elif "ui" in responsible_agent.lower():
                        responsible_agent = "Game_UI"
                    elif "scene" in responsible_agent.lower():
                        responsible_agent = "Scenes"
                    else:
                        if not is_historical:
                            print(f"{RED}Could not determine which agent is responsible for {unity_file}.{RESET}")
                            print(f"{YELLOW}Please select an agent:{RESET}")
                            for i, agent in enumerate(final_scripts.keys()):
                                print(f"{i+1}: {agent}")
                            selection = input("Enter number: ")
                            try:
                                idx = int(selection) - 1
                                responsible_agent = list(final_scripts.keys())[idx]
                            except Exception:
                                print(f"{RED}Invalid selection. Using Game_Manager as default.{RESET}")
                                responsible_agent = "Game_Manager"
                        else:
                            responsible_agent = "Game_Manager"

            print(f"{GREEN}Identified {responsible_agent} as responsible for {unity_file}{RESET}")
            current_script = final_scripts.get(responsible_agent, "")

            agents_dict = {
                'Game_Manager': (GameManagerAgent(), BLUE),
                'Game_Controller': (GameControllerAgent(), BLUE),
                'Game_UI': (GameUIAgent(), BLUE),
                'Scenes': (ScenesAgent(), BLUE),
            }
            agent_obj, color = agents_dict.get(responsible_agent, (None, RED))
            if not agent_obj:
                print(f"{RED}No agent object found for {responsible_agent}.{RESET}")
                return False

            line_match = re.search(r'LINE_NUMBER:\s*(\d+)', analysis)
            line_number = line_match.group(1) if line_match else "unknown"
            print(f"{color}Asking {responsible_agent} to fix the issue in {unity_file} at line {line_number}...{RESET}")

            fixed_feedback = f"""
Fix the following Unity compiler error in {unity_file}:

{error_message}

Analysis:
{analysis}

IMPORTANT INSTRUCTIONS:
1. You must regenerate ALL scripts in your markdown file, not just fix this one line.
2. Ensure ALL scripts have valid C# syntax with no unexpected characters.
3. Pay special attention to line {line_number} in {unity_file} where the error occurs.
4. Return the COMPLETE markdown file with ALL scripts properly formatted.
5. Remove any triple backticks or other markdown artifacts from actual script content.
"""
            updated_code = await agent_obj.handle_feedback(fixed_feedback, current_script)
            final_scripts[responsible_agent] = updated_code

            filename = f"{responsible_agent}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(updated_code)
            print(f"{GREEN}Saved updated {filename}{RESET}")

            extract_and_place_files(filename, project_path)
            print(f"{GREEN}Updated files extracted to Unity project{RESET}")

            print(f"{GREEN}Tester: All scripts from {responsible_agent} have been regenerated.{RESET}")
            return True

        # Process historical errors first.
        if error_history.get("errors"):
            print(f"{GREEN}==== Checking Historical Errors ===={RESET}")
            print(f"{GREEN}Found {len(error_history['errors'])} previous errors to check.{RESET}")
            fixed_count = 0
            for error_idx, error_data in enumerate(error_history["errors"]):
                print(f"{GREEN}Processing historical error {error_idx+1}/{len(error_history['errors'])}...{RESET}")
                success = await process_error(error_data["message"], is_historical=True)
                if success:
                    fixed_count += 1
            print(f"{GREEN}Finished processing historical errors. Fixed {fixed_count}/{len(error_history['errors'])}.{RESET}")
            if fixed_count > 0:
                print(f"{GREEN}Please try compiling your Unity project again to see if historical errors are resolved.{RESET}")
                user_input = input(f"{GREEN}Press Enter to continue to new error reporting, or type 'test' to test if historical errors are fixed: {RESET}")
                if user_input.lower() == 'test':
                    print(f"{GREEN}Skipping to next iteration to verify historical fixes.{RESET}")
                    error_history["errors"] = []
                    with open(error_history_file, 'w', encoding='utf-8') as f:
                        json.dump(error_history, f, indent=2)

        # Begin user feedback loop for new errors.
        while True:
            print(f"\n{GREEN}==== User Feedback Session ===={RESET}")
            print(f"{GREEN}Tester: Are there any new errors or issues you'd like me to address?{RESET}")
            print(f"{GREEN}(Type 'NO' to finish, or paste Unity error messages){RESET}")

            user_feedback = input("> ").strip()
            if user_feedback.upper() == "NO":
                print(f"{GREEN}Tester: Great! All issues have been addressed.{RESET}")
                break

            timestamp = datetime.datetime.now().isoformat()
            error_history["errors"].append({
                "timestamp": timestamp,
                "message": user_feedback
            })

            with open(error_history_file, 'w', encoding='utf-8') as f:
                json.dump(error_history, f, indent=2)
            print(f"{GREEN}Added error to history log.{RESET}")

            success = await process_error(user_feedback)
            if success:
                print(f"{GREEN}Please try compiling your Unity project again.{RESET}")
            else:
                print(f"{RED}Failed to process this error. Please provide more details.{RESET}")

        print(f"{GREEN}==== Code Generation Process Complete ===={RESET}")
    except Exception as e:
        print(f"{RED}Error in process_code_generation: {e}{RESET}")
        raise


# Class to store file content backup for rollback feature
class FileBackup:
    def __init__(self, filepath: str, content: str):
        self.filepath = filepath
        self.content = content


async def process_existing_game_edits() -> None:
    """
    Processes modifications for an existing Unity game using the Unity Code Editor agent.
    
    This function initializes the editor, scans the Unity project, and enters a user
    interaction loop to receive feature modification requests and apply them.
    Also includes a rollback feature to revert changes if needed.
    """
    try:
        print(f"{MAGENTA}==== Unity Code Editor ===={RESET}")
        print(f"{MAGENTA}Please select your Unity project directory in the file browser...{RESET}")
        
        project_path = browse_unity_project()
        if not project_path:
            print(f"{RED}No Unity project selected. Aborting.{RESET}")
            return
            
        print(f"{MAGENTA}Initializing editor for project: {project_path}{RESET}")

        from conf import Gemini_key  # Import API key for the Unity Code Editor
        editor_agent = UnityCodeEditorAgent(project_path=project_path, api_key=Gemini_key)
        editor_agent.scan_unity_project()

        # List to store file backups for rollback functionality
        session_backups: List[List[FileBackup]] = []

        while True:
            print(f"\n{MAGENTA}==== Unity Code Editor - Feature Request ===={RESET}")
            print(f"{MAGENTA}What would you like to modify in your Unity game?{RESET}")
            print(f"{MAGENTA}(Type 'EXIT' to finish editing){RESET}")

            user_request = input("> ").strip()
            if user_request.upper() == "EXIT":
                print(f"{MAGENTA}Unity Code Editor: Finished editing session.{RESET}")
                break

            print(f"{MAGENTA}Processing your request: {user_request}{RESET}")
            try:
                # Create backups before making changes
                current_backups: List[FileBackup] = []
                
                file_updates = await editor_agent.process_user_request(user_request)
                if not file_updates:
                    print(f"{RED}No files were modified for this request.{RESET}")
                    continue

                # Create backups of files that will be modified
                for update in file_updates:
                    filepath = update.filepath
                    try:
                        if os.path.exists(filepath):
                            with open(filepath, 'r', encoding='utf-8') as f:
                                original_content = f.read()
                            current_backups.append(FileBackup(filepath, original_content))
                            print(f"{CYAN}Created backup for: {filepath}{RESET}")
                    except Exception as e:
                        print(f"{RED}Error creating backup for {filepath}: {e}{RESET}")

                # Store backups for this edit session
                if current_backups:
                    session_backups.append(current_backups)

                print(f"\n{MAGENTA}==== Unity Code Editor - Changes Summary ===={RESET}")
                print(f"{MAGENTA}Modified {len(file_updates)} files:{RESET}")
                for update in file_updates:
                    print(f"{CYAN}- {update.filepath}{RESET}")

                print(f"\n{MAGENTA}Would you like to test these changes in Unity? (yes/no){RESET}")
                test_response = input("> ").strip().lower()
                if test_response in ("yes", "y"):
                    print(f"{MAGENTA}Please test your Unity project and report any errors.{RESET}")
                    print(f"{MAGENTA}Did you encounter any errors? (yes/no){RESET}")
                    error_response = input("> ").strip().lower()
                    
                    if error_response in ("yes", "y"):
                        print(f"{MAGENTA}Please paste the error message:{RESET}")
                        error_message = input("> ").strip()
                        
                        print(f"{MAGENTA}Would you like to rollback these changes and try a different approach? (yes/no){RESET}")
                        rollback_response = input("> ").strip().lower()
                        
                        if rollback_response in ("yes", "y"):
                            if session_backups:
                                last_backup = session_backups.pop()
                                print(f"{MAGENTA}Rolling back changes to {len(last_backup)} files...{RESET}")
                                
                                for backup in last_backup:
                                    try:
                                        with open(backup.filepath, 'w', encoding='utf-8') as f:
                                            f.write(backup.content)
                                        print(f"{GREEN}Restored: {backup.filepath}{RESET}")
                                    except Exception as e:
                                        print(f"{RED}Error restoring {backup.filepath}: {e}{RESET}")
                                        
                                print(f"{MAGENTA}All changes have been rolled back.{RESET}")
                            else:
                                print(f"{RED}No backups available to rollback.{RESET}")
                        else:
                            print(f"{MAGENTA}Attempting to fix the error...{RESET}")
                            refined_request = f"""
Fix the following error in my Unity game:

{error_message}

This was encountered after implementing the following feature:
{user_request}

Please analyze and fix all affected files.
"""
                            await editor_agent.process_user_request(refined_request)
                    else:
                        print(f"{MAGENTA}Great! Changes were successful.{RESET}")
                else:
                    print(f"{MAGENTA}Would you like to rollback these changes? (yes/no){RESET}")
                    rollback_response = input("> ").strip().lower()
                    
                    if rollback_response in ("yes", "y"):
                        if session_backups:
                            last_backup = session_backups.pop()
                            print(f"{MAGENTA}Rolling back changes to {len(last_backup)} files...{RESET}")
                            
                            for backup in last_backup:
                                try:
                                    with open(backup.filepath, 'w', encoding='utf-8') as f:
                                        f.write(backup.content)
                                    print(f"{GREEN}Restored: {backup.filepath}{RESET}")
                                except Exception as e:
                                    print(f"{RED}Error restoring {backup.filepath}: {e}{RESET}")
                                    
                            print(f"{MAGENTA}All changes have been rolled back.{RESET}")
                        else:
                            print(f"{RED}No backups available to rollback.{RESET}")
                    else:
                        print(f"{MAGENTA}Changes have been applied.{RESET}")
                        
            except Exception as e:
                print(f"{RED}Error processing your request: {e}{RESET}")

        print(f"{MAGENTA}==== Unity Code Editor Session Complete ===={RESET}")
    except Exception as e:
        print(f"{RED}Error in process_existing_game_edits: {e}{RESET}")
        raise


async def main() -> None:
    """
    Main entry point for the Unity Game Development System.
    
    Provides the user with the option to either:
      1. Create a new Unity game (generate all scripts from scratch), or
      2. Edit an existing Unity game (modify existing C# files).
    """
    print(f"{GREEN}==== Unity Game Development System ===={RESET}")
    print(f"{GREEN}Choose an option:{RESET}")
    print(f"{GREEN}1. Create a new Unity game (Generate all scripts from scratch){RESET}")
    print(f"{GREEN}2. Edit an existing Unity game (Modify existing CS files){RESET}")

    choice = input(f"{GREEN}Enter your choice (1 or 2): {RESET}").strip()

    if choice == "1":
        print(f"{GREEN}Creating a new Unity game...{RESET}")
        await process_code_generation()
    elif choice == "2":
        print(f"{GREEN}Editing an existing Unity game...{RESET}")
        await process_existing_game_edits()
    else:
        print(f"{RED}Invalid choice. Please run the script again and enter 1 or 2.{RESET}")

# if __name__ == "__main__":
#     asyncio.run(main())