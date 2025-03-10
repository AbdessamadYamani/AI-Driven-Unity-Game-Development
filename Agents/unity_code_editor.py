import os
import re
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from google import genai
from conf import Gemini_key
from PIL import Image
import imghdr


###################### Code editore Agent


# ANSI color codes
PURPLE = "\033[38;5;135m"  # Special color for Editor Agent
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"  # Add yellow for UI resource info
BLUE = "\033[94m"
RESET = "\033[0m"

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FileUpdate:
    filepath: str
    original_content: str
    updated_content: str
    changes_summary: str

@dataclass
class UIResource:
    filepath: str
    filename: str
    dimensions: Tuple[int, int]
    description: str

class UnityCodeEditorAgent:
    """Agent that directly edits CS files in an existing Unity project and accesses UI resources."""
    
    def __init__(self, project_path: str, api_key=None):
        self.client = genai.Client(api_key=api_key or Gemini_key)
        self.project_path = project_path
        self.cs_files: Dict[str, str] = {}  # Maps filepath to content
        self.ui_resources: Dict[str, UIResource] = {}  # Maps filepath to UIResource
        self.resources_scanned = False
        self.editor_chat = self.client.chats.create(model='gemini-2.0-flash-thinking-exp')
        
    def scan_unity_project(self) -> None:
        """Scan the Unity project directory and collect all .cs files."""
        print(f"{PURPLE}Scanning Unity project at {self.project_path}...{RESET}")
        
        cs_files_count = 0
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".cs"):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, self.project_path)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            self.cs_files[rel_path] = content
                            cs_files_count += 1
                    except Exception as e:
                        logger.error(f"Error reading file {filepath}: {e}")
        
        print(f"{PURPLE}Found {cs_files_count} C# files in the Unity project.{RESET}")
        
        # After scanning CS files, always scan UI resources
        self.scan_ui_resources()
    
    def scan_ui_resources(self) -> None:
        """Scan the Unity project's Resources directory for UI assets (PNG files)."""
        resources_path = os.path.join(self.project_path, "Resources")
        print(f"{YELLOW}Scanning UI resources at {resources_path}...{RESET}")
        
        if not os.path.exists(resources_path):
            print(f"{RED}Resources directory not found at {resources_path}{RESET}")
            return
        
        ui_resources_count = 0
        for root, _, files in os.walk(resources_path):
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, self.project_path)
                
                # Check if it's an image file
                if self._is_image_file(filepath):
                    try:
                        # Get image dimensions
                        with Image.open(filepath) as img:
                            dimensions = img.size
                        
                        # Generate description based on filename
                        filename = os.path.basename(filepath)
                        description = self._generate_resource_description(filename)
                        
                        # Store the UI resource info
                        self.ui_resources[rel_path] = UIResource(
                            filepath=rel_path,
                            filename=filename,
                            dimensions=dimensions,
                            description=description
                        )
                        ui_resources_count += 1
                    except Exception as e:
                        logger.error(f"Error processing UI resource {filepath}: {e}")
        
        self.resources_scanned = True
        print(f"{YELLOW}Found {ui_resources_count} UI resources in the Unity project.{RESET}")
        
        # Print some examples if resources were found
        if ui_resources_count > 0:
            print(f"{YELLOW}UI Resources Examples:{RESET}")
            for i, (path, resource) in enumerate(list(self.ui_resources.items())[:5]):  # Show up to 5 examples
                print(f"{YELLOW}- {resource.filename} ({resource.dimensions[0]}x{resource.dimensions[1]}): {resource.description}{RESET}")
            
            if ui_resources_count > 5:
                print(f"{YELLOW}... and {ui_resources_count - 5} more UI resources{RESET}")
    
    def _is_image_file(self, filepath: str) -> bool:
        """Check if a file is an image file."""
        try:
            # First check the extension
            if not filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tga')):
                return False
            
            # Then verify it's actually an image using imghdr
            img_type = imghdr.what(filepath)
            return img_type is not None
        except Exception:
            return False
    
    def _generate_resource_description(self, filename: str) -> str:
        """Generate a description of the UI resource based on its filename."""
        # Remove extension and split by common separators
        name = os.path.splitext(filename)[0]
        words = re.findall(r'[A-Z][a-z]*|[a-z]+|[0-9]+', name)
        clean_name = ' '.join(words).lower()
        
        # Map common UI element prefixes/keywords to descriptions
        ui_mappings = {
            'btn': 'Button',
            'button': 'Button',
            'icon': 'Icon',
            'bg': 'Background',
            'background': 'Background',
            'panel': 'Panel',
            'frame': 'Frame',
            'banner': 'Banner',
            'logo': 'Logo',
            'avatar': 'Avatar',
            'profile': 'Profile picture',
            'slider': 'Slider control',
            'toggle': 'Toggle switch',
            'checkbox': 'Checkbox',
            'input': 'Input field',
            'dialog': 'Dialog box',
            'menu': 'Menu',
            'notification': 'Notification',
            'popup': 'Popup',
            'health': 'Health indicator',
            'mana': 'Mana/Energy indicator',
            'coin': 'Currency',
            'gold': 'Currency',
            'gem': 'Premium currency',
            'inventory': 'Inventory',
            'item': 'Game item',
            'weapon': 'Weapon',
            'skill': 'Skill icon',
            'spell': 'Spell icon',
            'card': 'Card element',
            'portrait': 'Character portrait',
            'loading': 'Loading indicator',
        }
        
        # Check for style/theme keywords
        style_keywords = {
            'fantasy': 'Fantasy-themed',
            'medieval': 'Medieval-styled',
            'futuristic': 'Futuristic-styled',
            'sci-fi': 'Sci-fi themed',
            'cartoon': 'Cartoon-styled',
            'realistic': 'Realistic',
            'pixel': 'Pixel art',
            'dark': 'Dark-themed',
            'light': 'Light-themed',
            'wood': 'Wooden-styled',
            'stone': 'Stone-styled',
            'metal': 'Metallic',
            'gold': 'Golden',
            'silver': 'Silver',
            'magic': 'Magical',
            'glowing': 'Glowing',
        }
        
        # Try to identify the UI element type
        element_type = 'UI element'
        for keyword, description in ui_mappings.items():
            if keyword in clean_name:
                element_type = description
                break
        
        # Try to identify style/theme
        style = None
        for keyword, description in style_keywords.items():
            if keyword in clean_name:
                style = description
                break
        
        # Generate the final description
        if style:
            return f"{style} {element_type} ({clean_name})"
        else:
            return f"{element_type} ({clean_name})"
    
    def get_ui_resources_info(self) -> str:
        """Get information about available UI resources for the AI to use."""
        if not self.resources_scanned:
            self.scan_ui_resources()
        
        if not self.ui_resources:
            return "No UI resources found in the project."
        
        # Generate a summary of available UI resources
        resource_types = {}
        for resource in self.ui_resources.values():
            category = resource.description.split('(')[0].strip()
            if category in resource_types:
                resource_types[category].append(resource.filename)
            else:
                resource_types[category] = [resource.filename]
        
        # Build a summary text
        summary = ["Available UI Resources:"]
        for category, filenames in resource_types.items():
            summary.append(f"- {category}: {len(filenames)} files")
            # List up to 3 examples per category
            examples = filenames[:3]
            if examples:
                examples_str = ", ".join(examples)
                if len(filenames) > 3:
                    examples_str += f", ... ({len(filenames) - 3} more)"
                summary.append(f"  Examples: {examples_str}")
        
        return "\n".join(summary)
    
    async def analyze_request(self, user_request: str) -> Dict[str, List[str]]:
        """Analyze user request and identify relevant files to be modified."""
        print(f"{PURPLE}Analyzing user request: {user_request}{RESET}")
        
        # Make sure we have UI resources information
        if not self.resources_scanned:
            self.scan_ui_resources()
        
        # Create a summary of all files for the AI to analyze
        files_summary = []
        for filepath, content in self.cs_files.items():
            # Extract class names and key methods to make the summary more informative
            class_match = re.search(r'class\s+(\w+)', content)
            class_name = class_match.group(1) if class_match else "Unknown"
            
            # Get first 10 lines as a preview
            preview = "\n".join(content.split("\n")[:10]) + "\n..."
            
            files_summary.append(f"File: {filepath}\nClass: {class_name}\nPreview:\n{preview}\n")
        
        # Join summaries, but limit length to avoid token issues
        files_summary_text = "\n".join(files_summary[:50])  # Limit to 50 files
        if len(self.cs_files) > 50:
            files_summary_text += f"\n... and {len(self.cs_files) - 50} more files"
        
        # Include UI resources information
        ui_resources_info = self.get_ui_resources_info()
        
        prompt = f"""
You are a Unity Game Code Editor analyzing a request to modify an existing game.

USER REQUEST:
{user_request}

PROJECT FILES SUMMARY:
{files_summary_text}

UI RESOURCES INFORMATION:
{ui_resources_info}

1. Identify which files need to be modified to implement this request.
2. For each identified file, explain why it needs to be modified and what changes are needed.
3. Consider available UI resources when implementing UI-related changes.
4. The most important thing is that the goal is to create a whole game using only AND ONLY script the user should not interact with the GUI , create gameObjects ..etc , 100% Should be create only from script

Return your analysis in this format:
FILES_TO_MODIFY:
- [filepath1]: [reason for modification]
- [filepath2]: [reason for modification]
...

If you need to see the full content of specific files before making a final decision, list them like this:
FILES_TO_INSPECT:
- [filepath1]
- [filepath2]
...

If UI resources are needed for this implementation, specify them like this:
UI_RESOURCES_NEEDED:
- [filename1]: [purpose]
- [filename2]: [purpose]
...
"""
        
        response = await asyncio.to_thread(lambda: self.editor_chat.send_message(prompt))
        analysis = response.text.strip()
        
        print(f"{PURPLE}Initial Analysis:{RESET}\n{analysis}")
        
        # Parse the response to get lists of files
        files_to_modify = []
        files_to_inspect = []
        ui_resources_needed = []
        
        current_section = None
        for line in analysis.split('\n'):
            if line.startswith('FILES_TO_MODIFY:'):
                current_section = 'modify'
            elif line.startswith('FILES_TO_INSPECT:'):
                current_section = 'inspect'
            elif line.startswith('UI_RESOURCES_NEEDED:'):
                current_section = 'ui'
            elif line.strip().startswith('-') and current_section:
                item = line.strip()[1:].strip()
                if current_section == 'modify':
                    filepath = item.split(':')[0].strip()
                    filepath = re.sub(r'[\[\]]', '', filepath).strip()
                    files_to_modify.append(filepath)
                elif current_section == 'inspect':
                    filepath = item.split(':')[0].strip() if ':' in item else item
                    filepath = re.sub(r'[\[\]]', '', filepath).strip()
                    files_to_inspect.append(filepath)
                elif current_section == 'ui':
                    ui_resources_needed.append(item)
        
        # If there are UI resources needed, log them
        if ui_resources_needed:
            print(f"{YELLOW}UI Resources needed for implementation:{RESET}")
            for resource in ui_resources_needed:
                print(f"{YELLOW}- {resource}{RESET}")
        
        # If there are files to inspect, send their full content
        if files_to_inspect:
            print(f"{PURPLE}Agent needs to inspect {len(files_to_inspect)} files in detail.{RESET}")
            
            inspection_content = []
            for filepath in files_to_inspect:
                # Find the closest matching filepath
                matching_filepath = self._find_closest_file(filepath)
                if matching_filepath:
                    inspection_content.append(f"FILE: {matching_filepath}\n```csharp\n{self.cs_files[matching_filepath]}\n```\n")
            
            inspect_prompt = f"""
Based on the user request:
{user_request}

Here are the full contents of the files you requested to inspect:

{"\n".join(inspection_content)}

UI RESOURCES INFORMATION:
{ui_resources_info}

Now, provide your final analysis of which files need to be modified.
IMPORTANT: The most important thing is that the goal is to create a whole game using only AND ONLY script the user should not interact with the GUI , create gameObjects ..etc , 100% Should be create only from script

Return your analysis in this format:
FILES_TO_MODIFY:
- [filepath1]: [reason for modification]
- [filepath2]: [reason for modification]
...

If UI resources are needed for this implementation, specify them like this:
UI_RESOURCES_NEEDED:
- [filename1]: [purpose]
- [filename2]: [purpose]
...
"""
            
            response = await asyncio.to_thread(lambda: self.editor_chat.send_message(inspect_prompt))
            final_analysis = response.text.strip()
            
            print(f"{PURPLE}Final Analysis after inspection:{RESET}\n{final_analysis}")
            
            # Update the files to modify
            files_to_modify = []
            ui_resources_needed = []
            current_section = None
            for line in final_analysis.split('\n'):
                if line.startswith('FILES_TO_MODIFY:'):
                    current_section = 'modify'
                elif line.startswith('UI_RESOURCES_NEEDED:'):
                    current_section = 'ui'
                elif line.strip().startswith('-') and current_section:
                    item = line.strip()[1:].strip()
                    if current_section == 'modify':
                        parts = item.split(':', 1)
                        if parts:
                            filepath = re.sub(r'[\[\]]', '', parts[0]).strip()
                            files_to_modify.append(filepath)
                    elif current_section == 'ui':
                        ui_resources_needed.append(item)
        
        # Log any UI resources needed after final analysis
        if ui_resources_needed:
            print(f"{YELLOW}Final UI Resources needed for implementation:{RESET}")
            for resource in ui_resources_needed:
                print(f"{YELLOW}- {resource}{RESET}")
        
        # Find the closest matching files from our actual file list
        final_files_to_modify = {}
        for filepath in files_to_modify:
            matching_filepath = self._find_closest_file(filepath)
            if matching_filepath:
                reason = ""
                # Try to extract the reason from the analysis
                for line in analysis.split('\n') + (final_analysis.split('\n') if 'final_analysis' in locals() else []):
                    if filepath in line and ':' in line:
                        reason = line.split(':', 1)[1].strip()
                        break
                
                if matching_filepath not in final_files_to_modify:
                    final_files_to_modify[matching_filepath] = [reason]
                else:
                    final_files_to_modify[matching_filepath].append(reason)
        
        return final_files_to_modify
    
    def _find_closest_file(self, filepath: str) -> Optional[str]:
        """Find the closest matching file from self.cs_files."""
        if filepath in self.cs_files:
            return filepath
        
        # Try matching just the filename
        filename = os.path.basename(filepath)
        matching_files = [f for f in self.cs_files.keys() if os.path.basename(f) == filename]
        
        if matching_files:
            return matching_files[0]
        
        # Try a more fuzzy match - any file containing part of the name
        for existing_file in self.cs_files.keys():
            if filename.lower() in existing_file.lower():
                return existing_file
        
        return None
    
    async def modify_files(self, files_to_modify: Dict[str, List[str]], user_request: str) -> List[FileUpdate]:
        """Modify the identified files according to the user request."""
        updates = []
        
        # Make sure we have UI resources information
        if not self.resources_scanned:
            self.scan_ui_resources()
        
        # Generate UI resources information for the prompt
        ui_resources_info = self.get_ui_resources_info()
        
        for filepath, reasons in files_to_modify.items():
            print(f"{PURPLE}Modifying file: {filepath}{RESET}")
            original_content = self.cs_files[filepath]
            
            # Combine reasons if there are multiple
            combined_reason = "; ".join(reasons)
            
            prompt = f"""
You are a Unity Game Code Editor tasked with modifying a C# script.
IMPORTANT: The most important thing is that the goal is to create a whole game using only AND ONLY script the user should not interact with the GUI , create gameObjects ..etc , 100% Should be create only from script

USER REQUEST:
{user_request}

FILE TO MODIFY: {filepath}
REASON FOR MODIFICATION: {combined_reason}

ORIGINAL FILE CONTENT:
```csharp
{original_content}
```

UI RESOURCES INFORMATION:
{ui_resources_info}

Your task:
1. Carefully modify the code to implement the requested changes.
2. Maintain the original code structure where possible.
3. Add clear comments to explain your changes.
4. Ensure the code is syntactically correct C#.
5. If UI resources are needed, reference them by exact filename from the list above.
6. Return the COMPLETE updated file with ALL your changes.
7. The most important thing is that the goal is to create a whole game using only AND ONLY script the user should not interact with the GUI , create gameObjects ..etc , 100% Should be create only from script

First explain the specific changes you'll make, then provide the complete updated file content.
"""
            
            response = await asyncio.to_thread(lambda: self.editor_chat.send_message(prompt))
            response_text = response.text.strip()
            
            # Extract the updated code
            explanation = ""
            updated_content = original_content  # Default to original
            
            # Try to find code blocks
            code_blocks = re.findall(r'```(?:csharp)?\n(.*?)\n```', response_text, re.DOTALL)
            if code_blocks and len(code_blocks[-1]) > 100:  # Use the last code block if it's substantial
                updated_content = code_blocks[-1].strip()
                # Extract explanation from before the code block
                code_start = response_text.rfind("```", 0, response_text.rfind(updated_content))
                if code_start > 0:
                    explanation = response_text[:code_start].strip()
            else:
                # If no code blocks, look for a line that looks like the start of a file
                lines = response_text.split('\n')
                start_index = -1
                for i, line in enumerate(lines):
                    if line.startswith("using ") or line.startswith("namespace ") or line.startswith("public class "):
                        start_index = i
                        break
                
                if start_index >= 0:
                    updated_content = '\n'.join(lines[start_index:])
                    explanation = '\n'.join(lines[:start_index]).strip()
            
            # Verify the updated content is different and substantial
            if len(updated_content) < 50 or updated_content == original_content:
                print(f"{RED}Warning: Updated content for {filepath} appears invalid or unchanged.{RESET}")
                # Ask for clarification
                clarify_prompt = f"""
The updated code you provided for {filepath} doesn't appear to be complete or valid.
Please provide the FULL updated file content with your changes implemented.
Make sure to include ALL original code with your modifications integrated.
Don't summarize or abbreviate the code.
IMPORTANT: The most important thing is that the goal is to create a whole game using only AND ONLY script the user should not interact with the GUI , create gameObjects ..etc , 100% Should be create only from script

Remember to consider the UI resources available:
{ui_resources_info}
"""
                
                response = await asyncio.to_thread(lambda: self.editor_chat.send_message(clarify_prompt))
                response_text = response.text.strip()
                
                # Try extraction again
                code_blocks = re.findall(r'```(?:csharp)?\n(.*?)\n```', response_text, re.DOTALL)
                if code_blocks and len(code_blocks[-1]) > 100:
                    updated_content = code_blocks[-1].strip()
            
            # Create a diff summary
            from difflib import unified_diff
            diff = list(unified_diff(original_content.splitlines(), updated_content.splitlines(), lineterm=''))
            diff_summary = "\n".join(diff[:50])  # Limit to 50 lines
            if len(diff) > 50:
                diff_summary += f"\n... and {len(diff) - 50} more changes"
            
            # Check if UI resources are mentioned in the updated code
            ui_resources_used = []
            for resource in self.ui_resources.values():
                if resource.filename in updated_content:
                    ui_resources_used.append(resource.filename)
            
            if ui_resources_used:
                ui_resources_summary = f"\nUI Resources Used:\n- " + "\n- ".join(ui_resources_used)
            else:
                ui_resources_summary = "\nNo UI resources directly referenced in code."
            
            update = FileUpdate(
                filepath=filepath,
                original_content=original_content,
                updated_content=updated_content,
                changes_summary=f"Explanation:\n{explanation}\n\nChanges:\n{diff_summary}\n{ui_resources_summary}"
            )
            
            updates.append(update)
            
            # Update our copy of the file
            self.cs_files[filepath] = updated_content
        
        return updates
    
    async def write_updates_to_disk(self, updates: List[FileUpdate], backup: bool = True) -> None:
        """Write the updated file contents to disk, with optional backup."""
        print(f"{PURPLE}Writing {len(updates)} file updates to disk...{RESET}")
        
        for update in updates:
            full_path = os.path.join(self.project_path, update.filepath)
            
            # Create backup if requested
            if backup:
                backup_path = f"{full_path}.bak"
                try:
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(update.original_content)
                    print(f"{PURPLE}Created backup: {backup_path}{RESET}")
                except Exception as e:
                    logger.error(f"Error creating backup for {full_path}: {e}")
            
            # Write updated file
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(update.updated_content)
                print(f"{GREEN}Updated file: {full_path}{RESET}")
            except Exception as e:
                logger.error(f"Error writing to file {full_path}: {e}")
    
    async def process_user_request(self, user_request: str) -> List[FileUpdate]:
        """Process a user request to modify the Unity game."""
        print(f"{PURPLE}==== Processing User Request ===={RESET}")
        print(f"{PURPLE}Request: {user_request}{RESET}")
        
        # 1. Scan Unity project for CS files if not already done
        if not self.cs_files:
            self.scan_unity_project()
        else:
            # Make sure UI resources are scanned even if CS files were already scanned
            if not self.resources_scanned:
                self.scan_ui_resources()
        
        # Display UI resources status
        if self.resources_scanned:
            if self.ui_resources:
                print(f"{GREEN}✓ Successfully accessed {len(self.ui_resources)} UI resources in /Resources{RESET}")
            else:
                print(f"{YELLOW}⚠ No UI resources found in /Resources{RESET}")
        else:
            print(f"{RED}✗ Failed to access UI resources in /Resources{RESET}")
        
        # 2. Analyze request to identify files to modify
        files_to_modify = await self.analyze_request(user_request)
        
        if not files_to_modify:
            print(f"{RED}No files identified for modification.{RESET}")
            return []
        
        print(f"{PURPLE}Files identified for modification:{RESET}")
        for filepath, reasons in files_to_modify.items():
            print(f"{PURPLE}- {filepath}: {'; '.join(reasons)}{RESET}")
        
        # 3. Modify identified files
        updates = await self.modify_files(files_to_modify, user_request)
        
        # 4. Preview changes
        print(f"{PURPLE}==== Preview of Changes ===={RESET}")
        for update in updates:
            print(f"{PURPLE}File: {update.filepath}{RESET}")
            print(f"{PURPLE}{update.changes_summary}{RESET}")
            print()
        
        # 5. Write changes to disk
        await self.write_updates_to_disk(updates)
        
        return updates