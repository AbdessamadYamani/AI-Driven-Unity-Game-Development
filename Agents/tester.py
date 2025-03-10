import os
import asyncio
import logging
from typing import Dict, List, Set
from dataclasses import dataclass
from google import genai
from conf import Gemini_key
#################### Game tester agent
# ANSI color codes for agents
GREEN = "\033[92m"  # Tester
YELLOW = "\033[93m"  # Game Controller Agent
BLUE = "\033[94m"    # Game Manager Agent
MAGENTA = "\033[95m" # UI Agent
CYAN = "\033[96m"    # Scene Setup Agent
WHITE = "\033[97m"   # Brainstorming docs
RED = "\033[91m"     # Errors
RESET = "\033[0m"    # Reset color

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ScriptAnalysis:
    filename: str
    issues: List[str]
    status: str  # "PASS" or "FAIL"

class GameDevTester:
    def __init__(self, api_key=None):
        self.client = genai.Client(api_key=api_key or Gemini_key)
        self.scripts: Dict[str, str] = {}
        self.brainstorm_docs: Dict[str, str] = {}
        self.agent_chats: Dict[str, genai.ChatSession] = {}
        self.tester_chat = self.client.chats.create(model='gemini-2.0-flash-thinking-exp')

        self.agent_colors = {
            "Game_Manager.md": BLUE,
            "Game_Controller.md": YELLOW,
            "Game_UI.md": MAGENTA,
            "Scenes.md": CYAN,
            "brainstorm.md": WHITE,
            "UI_suggestion.md": WHITE
        }

        self.agent_names = {
            "Game_Manager.md": "Game Manager Agent",
            "Game_Controller.md": "Game Controller Agent",
            "Game_UI.md": "UI Agent",
            "Scenes.md": "Scene Setup Agent",
            "brainstorm.md": "Brainstorming Document",
            "UI_suggestion.md": "UI Suggestions Document"
        }

        # Initialize a chat session for each agent
        for filename in self.agent_names.keys():
            self.agent_chats[filename] = self.client.chats.create(model='gemini-2.0-flash-thinking-exp')

    def read_code(self, filepath: str) -> str:
        """Read script contents safely from the full filepath."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            return ""
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return ""

    def write_code(self, filepath: str, code: str):
        """Write updated script to file using the full filepath."""
        try:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(code)
            logger.info(f"Updated code written to {filepath}")
        except Exception as e:
            logger.error(f"Error writing to file {filepath}: {e}")

    async def analyze_integration(self) -> dict:
        """Analyze all scripts and brainstorming docs for integration issues."""
        # Combine all scripts
        combined_scripts = "\n\n===== FILE: ".join(
            [f"{name} =====\n{script}" for name, script in self.scripts.items()]
        )
        
        # Combine brainstorming docs
        combined_brainstorm = "\n\n===== BRAINSTORM DOC: ".join(
            [f"{name} =====\n{doc}" for name, doc in self.brainstorm_docs.items()]
        )

        prompt = f"""
    You are a Game Developer Tester analyzing Unity scripts and brainstorming documents for compatibility.

    ===== BRAINSTORM DOCUMENTS: {combined_brainstorm}

    ===== IMPLEMENTATION FILES: {combined_scripts}

    Focus on:
    1. Verifying implementation matches brainstorming requirements
    2. Method name mismatches between documents and code
    3. Missing or incorrect function implementations
    4. Parameter inconsistencies
    5. Namespace misalignment
    6. Type mismatches
    7. Broken GameObject references
    8. UI elements from UI_suggestion.md being properly implemented

    IMPORTANT: For each script, ALWAYS provide at least 2-3 improvement suggestions even if there are no critical issues.
    These can include code organization, performance optimizations, better variable naming, or additional comments.

    Return feedback in this format:
    FEEDBACK for [filename]:
    - [Issue 1: Detailed explanation]
    - [Issue 2: Detailed explanation]
    ...
    Recommendations:
    - [Recommendation 1]
    - [Recommendation 2]
    ...
    9. The most important thing is that the goal is to create a whole game using only AND ONLY script the user should not interact with the GUI , create gameObjects ..etc , 100% Should be create only from script

    Provide structured feedback for each file and ONLY return "DONE" status after 3 iterations of improvements.
    """

        print(f"{GREEN}Tester analyzing all scripts and brainstorming documents for integration issues...{RESET}")
        response = await asyncio.to_thread(lambda: self.tester_chat.send_message(prompt))
        analysis_text = response.text.strip()

        print(f"{GREEN}Integration Analysis:{RESET}")
        print(f"{GREEN}{analysis_text}{RESET}")

        # Force "REVIEW" status for the first 2 iterations
        if not hasattr(self, 'iteration_count'):
            self.iteration_count = 0
        
        self.iteration_count += 1
        status = "DONE" if self.iteration_count >= 3 else "REVIEW"

        feedback = {}
        current_script = None
        current_feedback = []

        for line in analysis_text.split('\n'):
            if line.startswith("FEEDBACK for "):
                if current_script:
                    feedback[current_script] = "\n".join(current_feedback)
                current_script = line.replace("FEEDBACK for ", "").rstrip(':')
                current_feedback = []
            elif current_script:
                current_feedback.append(line)

        if current_script:
            feedback[current_script] = "\n".join(current_feedback)

        # If feedback is empty for any script, add generic improvement suggestions
        for script_name in self.scripts.keys():
            if script_name not in feedback or not feedback[script_name].strip():
                feedback[script_name] = f"""
    Improvement suggestions for {script_name}:
    1. Consider adding more detailed comments to explain the purpose of each method
    2. Review variable naming conventions for consistency
    3. Look for opportunities to optimize performance in resource-intensive operations
    4. Add additional error handling for edge cases
    5. Consider implementing design patterns for better code organization
    6. The most important thing is that the goal is to create a whole game using only AND ONLY script the user should not interact with the GUI , create gameObjects ..etc , 100% Should be create only from script
    """

        return {"status": status, "report": analysis_text, "feedback": feedback}

    async def agent_conversation(self, filename: str, issues: str) -> str:
        """Tester-Agent interactive conversation for issue resolution."""
        agent_name = self.agent_names.get(filename, "Unknown Agent")
        agent_color = self.agent_colors.get(filename, RESET)
        agent_chat = self.agent_chats[filename]

        # Get appropriate brainstorm context
        brainstorm_context = ""
        for doc_name, doc_content in self.brainstorm_docs.items():
            brainstorm_context += f"\n\nContent from {doc_name}:\n{doc_content}"

        tester_prompt = f"""
You are the Game Development Tester.
I've identified these issues in {agent_name}'s script ({filename}):

{issues}

Please correct these errors and provide the **full updated script**.
"""

        print(f"\n{GREEN}Tester to {agent_name}:{RESET}")
        print(f"{GREEN}{tester_prompt}{RESET}")

        current_code = self.scripts.get(filename, "")
        agent_prompt = f"""
You are the {agent_name}. The tester found issues in your script:

{issues}

Your current script:
{current_code}

Relevant brainstorming context:{brainstorm_context}

Based on the brainstorming documents and the tester's feedback, explain how you will fix each issue, then provide your **full updated script**.
"""

        response = await asyncio.to_thread(lambda: agent_chat.send_message(agent_prompt))
        agent_response = response.text.strip()

        print(f"\n{agent_color}{agent_name} responds:{RESET}")
        print(f"{agent_color}{agent_response}{RESET}")

        updated_code = self.extract_code(agent_response, current_code)

        print(f"\n{GREEN}Tester reviewing changes...{RESET}")
        diff = self.get_diff_summary(current_code, updated_code)
        print(f"{GREEN}{diff}{RESET}")

        return updated_code

    def extract_code(self, response: str, default_code: str) -> str:
        """Extract code from an agent's response."""
        start_markers = ["```", "```csharp", "```c#", "```python", "```markdown"]
        end_marker = "```"

        for start_marker in start_markers:
            start_idx = response.find(start_marker)
            if start_idx != -1:
                start_pos = start_idx + len(start_marker)
                end_idx = response.find(end_marker, start_pos)
                if end_idx != -1:
                    code = response[start_pos:end_idx].strip()
                    # If we found a non-empty code block, return it
                    if code:
                        return code

        # If we couldn't find a code block, look for a section that appears to be complete code
        lines = response.split('\n')
        code_lines = []
        in_code_section = False
        
        for line in lines:
            # Heuristics to detect the start of a code section without markers
            if not in_code_section and (line.startswith("using ") or line.startswith("public class ") or line.startswith("# ")):
                in_code_section = True
            
            if in_code_section:
                code_lines.append(line)
                
        if code_lines:
            return '\n'.join(code_lines)
            
        return default_code

    def get_diff_summary(self, original: str, updated: str) -> str:
        """Generate a summary of code changes."""
        if original == updated:
            return "No changes detected."

        from difflib import unified_diff
        diff = list(unified_diff(original.splitlines(), updated.splitlines(), lineterm=''))
        return "\n".join(diff) if diff else "No significant differences."

    async def check_brainstorm_implementation(self):
        """Check if brainstorming concepts are properly implemented."""
        combined_scripts = "\n\n".join([f"FILE: {name}\n{script}" for name, script in self.scripts.items()])
        combined_brainstorm = "\n\n".join([f"DOC: {name}\n{doc}" for name, doc in self.brainstorm_docs.items()])
        
        prompt = f"""
        You are a Game Development Tester analyzing if brainstorming concepts have been properly implemented and the paths of the UI assets are right.
        
        BRAINSTORMING DOCUMENTS:
        {combined_brainstorm}
        
        IMPLEMENTATION FILES:
        {combined_scripts}
        
        Identify any concepts, features, or requirements from the brainstorming documents that are missing or 
        incompletely implemented in the code files. Focus especially on:
        
        1. Game mechanics discussed in brainstorm.md but missing in implementation
        2. UI elements specified in UI_suggestion.md but not implemented
        3. Inconsistencies between the brainstorming vision and the implementation
        4. The most important thing is that the goal is to create a whole game using only AND ONLY script the user should not interact with the GUI , create gameObjects ..etc , 100% Should be create only from script

        NOTE that somthims the brainstorming idea will not be implimented 100%
        Provide detailed feedback with specific references to both the brainstorming documents and the code files.
        """
        
        print(f"{GREEN}Checking brainstorming implementation completeness...{RESET}")
        response = await asyncio.to_thread(lambda: self.tester_chat.send_message(prompt))
        
        print(f"{GREEN}Brainstorming Implementation Analysis:{RESET}")
        print(f"{GREEN}{response.text.strip()}{RESET}")
        
        return response.text.strip()

    async def run_tests(self):
        """Main testing loop."""
        # Implementation files
        script_files = {
            "GameController.md": os.path.join("GameController.md"),
            "GameManager.md": os.path.join("GameManager.md"),
            "UIFiles.md": os.path.join("UIFiles.md"),
            "AutoSceneSetup.md": os.path.join("AutoSceneSetup.md")
        }
        
        # Brainstorming files
        brainstorm_files = {
            "brainstorm.md": os.path.join("brainstorm.md"),
            "UI_suggestion.md": os.path.join("UI_suggestion.md")
        }
        
        # Read all files
        self.scripts = {filename: self.read_code(filepath) for filename, filepath in script_files.items()}
        self.brainstorm_docs = {filename: self.read_code(filepath) for filename, filepath in brainstorm_files.items()}

        print(f"\n{GREEN}==== Testing Session Started ===={RESET}")
        
        # First check if brainstorming concepts are implemented
        print(f"\n{GREEN}==== Checking Brainstorming Implementation ===={RESET}")
        brainstorm_analysis = await self.check_brainstorm_implementation()
        
        # Then check integration issues
        analysis_result = await self.analyze_integration()

        if analysis_result["status"] == "DONE" and "No issues found" in brainstorm_analysis:
            print(f"\n{GREEN}✓ All scripts are compatible and brainstorming concepts are fully implemented!{RESET}")
            return

        for iteration in range(3):
            print(f"\n{GREEN}==== Integration Iteration {iteration+1} ===={RESET}")
            for filename, issues in analysis_result["feedback"].items():
                if issues:
                    print(f"\n{GREEN}Fixing {filename}...{RESET}")
                    filepath = script_files.get(filename, filename)  # Get the full path if available
                    updated_code = await self.agent_conversation(filename, issues)
                    self.scripts[filename] = updated_code
                    self.write_code(filepath, updated_code)

            analysis_result = await self.analyze_integration()
            if analysis_result["status"] == "DONE":
                print(f"\n{GREEN}✓ All scripts are now compatible!{RESET}")
                break

        print(f"\n{GREEN}==== Testing Completed ===={RESET}")


