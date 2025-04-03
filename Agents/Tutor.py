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
import datetime,textwrap
from collections import defaultdict
# Import the scene analysis function
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from watchdog_tool import comprehensive_scene_analysis
import msvcrt  # Windows-specific module for keyboard input

# Color codes
GREEN = "\033[92m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
YELLOW = "\033[93m"
try:
    import docx  # For Word document generation
except ImportError:
    print(f"{YELLOW}python-docx not installed. Will use text file for reports instead.{RESET}")
    print(f"{BLUE}To install: pip install python-docx{RESET}")


def validate_gdd_with_octalysis(gemini_client, gdd_content: str) -> Dict:
    """Validate the Game Design Document using Gemini AI and the Octalysis Framework"""
    try:
        # Suppress GRPC warnings
        
        # Octalysis framework prompt
        prompt = f"""
        You are a game design expert specializing in gamification through the Octalysis Framework.
        
        Analyze the following Game Design Document for a dyslexia support educational game:
        
        {gdd_content}
        
        Instructions:
        1. Evaluate how well the GDD incorporates the 8 core drives of the Octalysis Framework:
           - Epic Meaning & Calling
           - Development & Accomplishment
           - Empowerment of Creativity & Feedback
           - Ownership & Possession
           - Social Influence & Relatedness
           - Scarcity & Impatience
           - Unpredictability & Curiosity
           - Loss & Avoidance
        
        2. For each core drive:
           - Score the implementation on a scale of 1-10
           - Provide specific examples from the GDD that demonstrate the core drive
           - Suggest concrete improvements to strengthen this aspect
        
        3. Provide overall recommendations for gamification improvements
        
        4. Structure your response as a JSON object with the following format:
        {{
          "summary": "Brief overall assessment",
          "octalysis_scores": {{
            "epic_meaning": {{ "score": x, "examples": ["..."], "improvements": ["..."] }},
            "development": {{ "score": x, "examples": ["..."], "improvements": ["..."] }},
            "creativity": {{ "score": x, "examples": ["..."], "improvements": ["..."] }},
            "ownership": {{ "score": x, "examples": ["..."], "improvements": ["..."] }},
            "social": {{ "score": x, "examples": ["..."], "improvements": ["..."] }},
            "scarcity": {{ "score": x, "examples": ["..."], "improvements": ["..."] }},
            "unpredictability": {{ "score": x, "examples": ["..."], "improvements": ["..."] }},
            "loss_avoidance": {{ "score": x, "examples": ["..."], "improvements": ["..."] }}
          }},
          "overall_score": x,
          "top_recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"],
          "implementation_priority": ["High priority item 1", "High priority item 2"]
        }}
        """
        
        # Generate Gemini response
        response = gemini_client.generate_content(prompt)
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            validation_results = json.loads(json_match.group(0))
            return validation_results
        else:
            raise ValueError("Could not extract JSON from Gemini response")
            
    except Exception as e:
        print(f"{RED}Error validating GDD: {e}{RESET}")
        return {
            "summary": "Error occurred during validation",
            "error": str(e)
        }

def save_validation_report(validation_results: Dict, output_path: str, refinement_suggestions: str = None) -> str:
    """
    Save validation results to a Word document
    
    Args:
        validation_results (Dict): Results from GDD validation
        output_path (str): Base path to save the report
        refinement_suggestions (str): Optional refinement suggestions to append
        
    Returns:
        str: Path to the saved document
    """
    try:
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        # Create document
        doc = Document()
        
        # Add title
        title = doc.add_heading('Game Design Document Validation Report', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add summary
        doc.add_heading('Executive Summary', 1)
        doc.add_paragraph(validation_results['summary'])
        
        # Add overall score
        doc.add_heading('Overall Octalysis Score', 1)
        overall_para = doc.add_paragraph()
        overall_para.add_run(f"{validation_results['overall_score']}/10").bold = True
        
        # Add core drives analysis
        doc.add_heading('Core Drives Analysis', 1)
        
        # Define color coding for scores
        def get_score_color(score):
            if score <= 3:
                return RGBColor(240, 0, 0)  # Red
            elif score <= 6:
                return RGBColor(255, 165, 0)  # Orange
            else:
                return RGBColor(0, 128, 0)  # Green
        
        # Process each core drive
        for drive, details in validation_results['octalysis_scores'].items():
            score = details['score']
            drive_name = drive.replace('_', ' ').title()
            
            # Add heading for core drive
            heading = doc.add_heading(f"{drive_name}: ", 2)
            score_run = heading.add_run(f"{score}/10")
            score_run.font.color.rgb = get_score_color(score)
            
            # Examples section
            if details['examples']:
                doc.add_heading("Current Implementation:", 3)
                examples_para = doc.add_paragraph()
                for example in details['examples']:
                    examples_para.add_run(f"• {example}\n")
            
            # Improvements section
            if details['improvements']:
                doc.add_heading("Suggested Improvements:", 3)
                improvements_para = doc.add_paragraph()
                for improvement in details['improvements']:
                    improvements_para.add_run(f"• {improvement}\n")
                    
        # Add top recommendations
        doc.add_heading('Top Recommendations', 1)
        for recommendation in validation_results['top_recommendations']:
            doc.add_paragraph(f"• {recommendation}")
            
        # Add implementation priorities
        doc.add_heading('Implementation Priorities', 1)
        for priority in validation_results['implementation_priority']:
            doc.add_paragraph(f"• {priority}")
            
        # Add refinement suggestions if provided
        if refinement_suggestions:
            doc.add_heading('Refinement Suggestions', 1)
            doc.add_paragraph(refinement_suggestions)
            
        # Save document
        import os
        report_path = os.path.join(output_path, 'GDD_Validation_Report.docx')
        doc.save(report_path)
        
        return report_path
        
    except ImportError:
        # Fallback to text file if docx is not available
        import os
        report_path = os.path.join(output_path, 'GDD_Validation_Report.txt')
        
        with open(report_path, 'w') as f:
            f.write("GAME DESIGN DOCUMENT VALIDATION REPORT\n")
            f.write("====================================\n\n")
            f.write(f"EXECUTIVE SUMMARY:\n{validation_results['summary']}\n\n")
            f.write(f"OVERALL SCORE: {validation_results['overall_score']}/10\n\n")
            
            f.write("CORE DRIVES ANALYSIS:\n")
            for drive, details in validation_results['octalysis_scores'].items():
                drive_name = drive.replace('_', ' ').title()
                f.write(f"\n{drive_name}: {details['score']}/10\n")
                
                f.write("Current Implementation:\n")
                for example in details['examples']:
                    f.write(f"• {example}\n")
                    
                f.write("Suggested Improvements:\n")
                for improvement in details['improvements']:
                    f.write(f"• {improvement}\n")
            
            f.write("\nTOP RECOMMENDATIONS:\n")
            for recommendation in validation_results['top_recommendations']:
                f.write(f"• {recommendation}\n")
                
            f.write("\nIMPLEMENTATION PRIORITIES:\n")
            for priority in validation_results['implementation_priority']:
                f.write(f"• {priority}\n")
            
            # Add refinement suggestions if provided
            if refinement_suggestions:
                f.write("\nREFINEMENT SUGGESTIONS:\n")
                f.write("=======================\n\n")
                f.write(refinement_suggestions)
        
        return report_path
    except Exception as e:
        print(f"{RED}Error saving validation report: {e}{RESET}")
        return None


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

class MetricsLogger:
    def __init__(self, project_path: str):
        self.metrics_file = os.path.join(project_path, 'learning_metrics.md')
        self.metrics = {
            'start_time': datetime.datetime.now().isoformat(),
            'end_time': None,
            'gdd_refinements': 0,
            'tasks': defaultdict(dict),
            'chapters': defaultdict(dict),
            'coin_transactions': [],
            'script_purchases': 0,
            'scene_analysis_count': 0,
            'validation_attempts': defaultdict(int),
            'menu_accesses': 0,
            'current_coins': 0,
            'errors': []
        }
        # Create initial metrics file
        self._save_metrics()
    
    def log_task_start(self, chapter_num: int, task_num: int, task_title: str):
        """Record when a task begins"""
        task_key = f"chapter_{chapter_num}_task_{task_num}"
        self.metrics['tasks'][task_key] = {
            'title': task_title,
            'start_time': datetime.datetime.now().isoformat(),
            'end_time': None,
            'completed': False,
            'validation_attempts': 0
        }
        self._save_metrics()
    
    def log_task_completion(self, chapter_num: int, task_num: int, success: bool):
        """Record when a task is completed"""
        task_key = f"chapter_{chapter_num}_task_{task_num}"
        if task_key in self.metrics['tasks']:
            self.metrics['tasks'][task_key]['end_time'] = datetime.datetime.now().isoformat()
            self.metrics['tasks'][task_key]['completed'] = success
            if 'start_time' in self.metrics['tasks'][task_key]:
                start = datetime.datetime.fromisoformat(self.metrics['tasks'][task_key]['start_time'])
                end = datetime.datetime.now()
                self.metrics['tasks'][task_key]['duration_seconds'] = (end - start).total_seconds()
        self._save_metrics()
    
    def log_chapter_start(self, chapter_num: int, chapter_title: str):
        """Record when a chapter begins"""
        chapter_key = f"chapter_{chapter_num}"
        self.metrics['chapters'][chapter_key] = {
            'title': chapter_title,
            'start_time': datetime.datetime.now().isoformat(),
            'end_time': None,
            'completed': False
        }
        self._save_metrics()
    
    def log_chapter_completion(self, chapter_num: int):
        """Record when a chapter is completed"""
        chapter_key = f"chapter_{chapter_num}"
        if chapter_key in self.metrics['chapters']:
            self.metrics['chapters'][chapter_key]['end_time'] = datetime.datetime.now().isoformat()
            self.metrics['chapters'][chapter_key]['completed'] = True
            if 'start_time' in self.metrics['chapters'][chapter_key]:
                start = datetime.datetime.fromisoformat(self.metrics['chapters'][chapter_key]['start_time'])
                end = datetime.datetime.now()
                self.metrics['chapters'][chapter_key]['duration_seconds'] = (end - start).total_seconds()
        self._save_metrics()
    
    def log_gdd_refinement(self):
        """Record when GDD is refined"""
        self.metrics['gdd_refinements'] += 1
        self._save_metrics()
    
    def log_coin_transaction(self, amount: int, reason: str, current_balance: int):
        """Record coin transactions"""
        self.metrics['coin_transactions'].append({
            'timestamp': datetime.datetime.now().isoformat(),
            'amount': amount,
            'reason': reason,
            'balance': current_balance
        })
        self.metrics['current_coins'] = current_balance
        self._save_metrics()
    
    def log_script_purchase(self):
        """Record when full script is purchased"""
        self.metrics['script_purchases'] += 1
        self._save_metrics()
    
    def log_scene_analysis(self):
        """Record scene analysis events"""
        self.metrics['scene_analysis_count'] += 1
        self._save_metrics()
    
    def log_validation_attempt(self, chapter_num: int, task_num: int):
        """Record validation attempts"""
        task_key = f"chapter_{chapter_num}_task_{task_num}"
        self.metrics['validation_attempts'][task_key] += 1
        if task_key in self.metrics['tasks']:
            self.metrics['tasks'][task_key]['validation_attempts'] = self.metrics['validation_attempts'][task_key]
        self._save_metrics()
    
    def log_menu_access(self):
        """Record when user accesses the menu"""
        self.metrics['menu_accesses'] += 1
        self._save_metrics()
    
    def log_error(self, error: str):
        """Record errors that occur"""
        self.metrics['errors'].append({
            'timestamp': datetime.datetime.now().isoformat(),
            'error': error
        })
        self._save_metrics()
    
    def log_session_end(self):
        """Record when the session ends"""
        self.metrics['end_time'] = datetime.datetime.now().isoformat()
        if 'start_time' in self.metrics:
            start = datetime.datetime.fromisoformat(self.metrics['start_time'])
            end = datetime.datetime.now()
            self.metrics['total_duration_seconds'] = (end - start).total_seconds()
        self._save_metrics()
    
    def _save_metrics(self):
        """Save metrics to markdown file"""
        try:
            with open(self.metrics_file, 'w') as f:
                f.write(self._format_metrics())
        except Exception as e:
            print(f"{RED}Error saving metrics: {e}{RESET}")
    
    def _format_metrics(self) -> str:
        """Format metrics as markdown"""
        md = "# Unity Learning Tutor Metrics Report\n\n"
        md += f"## Session Overview\n"
        md += f"- **Start Time**: {self.metrics['start_time']}\n"
        md += f"- **End Time**: {self.metrics.get('end_time', 'Session in progress')}\n"
        if 'total_duration_seconds' in self.metrics:
            md += f"- **Total Duration**: {self.metrics['total_duration_seconds']:.2f} seconds\n"
        md += f"- **GDD Refinements**: {self.metrics['gdd_refinements']}\n"
        md += f"- **Script Purchases**: {self.metrics['script_purchases']}\n"
        md += f"- **Scene Analyses**: {self.metrics['scene_analysis_count']}\n"
        md += f"- **Menu Accesses**: {self.metrics['menu_accesses']}\n"
        md += f"- **Current Coin Balance**: {self.metrics['current_coins']}\n\n"
        
        md += "## Coin Transactions\n"
        md += "| Timestamp | Amount | Reason | Balance |\n"
        md += "|-----------|--------|--------|---------|\n"
        for tx in self.metrics['coin_transactions']:
            md += f"| {tx['timestamp']} | {tx['amount']} | {tx['reason']} | {tx['balance']} |\n"
        md += "\n"
        
        md += "## Chapter Progress\n"
        for chapter_key, chapter_data in self.metrics['chapters'].items():
            md += f"### {chapter_key.replace('_', ' ').title()}: {chapter_data.get('title', '')}\n"
            md += f"- Started: {chapter_data.get('start_time', 'N/A')}\n"
            md += f"- Completed: {chapter_data.get('end_time', 'Not completed')}\n"
            if 'duration_seconds' in chapter_data:
                md += f"- Duration: {chapter_data['duration_seconds']:.2f} seconds\n"
            md += "\n"
        
        md += "## Task Details\n"
        for task_key, task_data in self.metrics['tasks'].items():
            md += f"### {task_key.replace('_', ' ').title()}: {task_data.get('title', '')}\n"
            md += f"- Started: {task_data.get('start_time', 'N/A')}\n"
            md += f"- Completed: {task_data.get('end_time', 'Not completed')}\n"
            md += f"- Success: {task_data.get('completed', 'N/A')}\n"
            md += f"- Validation Attempts: {task_data.get('validation_attempts', 0)}\n"
            if 'duration_seconds' in task_data:
                md += f"- Duration: {task_data['duration_seconds']:.2f} seconds\n"
            md += "\n"
        
        md += "## Errors\n"
        if self.metrics['errors']:
            md += "| Timestamp | Error |\n"
            md += "|-----------|-------|\n"
            for error in self.metrics['errors']:
                md += f"| {error['timestamp']} | {error['error']} |\n"
        else:
            md += "No errors recorded.\n"
        md += "\n"
        
        md += "## Learning Path\n"
        md += "```json\n"
        md += json.dumps(self.metrics.get('learning_path', {}), indent=2)
        md += "\n```\n"
        
        return md

class UnityLearningTutor:
    def __init__(self, gemini_api_key: str, project_path: str, gdd_content: str):
        # Initialize Gemini AI
        genai.configure(api_key=gemini_api_key)
        self.gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.metrics_logger = MetricsLogger(project_path)

        # Project and learning path attributes
        self.project_path = project_path
        self.learning_path = {}
        self.current_chapter_index = 0
        self.current_task_index = 0
        self.gdd_content = gdd_content
        self.user_coins = 0
        self.script_detail_level = "Give only the functions and description of each one"
        self.coin_rewards = {
            "task_completion": 5,  # Coins earned for completing a task
            "chapter_completion": 15  # Additional coins for completing a chapter
        }
        self.coin_costs = {
            "full_script": 10  # Cost to get full script implementation
        }
        
        # Add to existing progress tracking
        self.progress_file = os.path.join(project_path, 'dyslexia_game_progress.json')
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

    def display_coin_status(self):
        """
        Display current coin balance and available actions
        """
        print(f"\n{CYAN}=========== COIN BALANCE ==========={RESET}")
        print(f"{GREEN}You have {self.user_coins} coins{RESET}")
        print(f"{BLUE}Available actions:{RESET}")
        print(f"- Complete tasks to earn {self.coin_rewards['task_completion']} coins")
        print(f"- Complete chapters to earn {self.coin_rewards['chapter_completion']} additional coins")
        print(f"- Purchase full script implementation for {self.coin_costs['full_script']} coins")
        print(f"- Get a Bonus for 60 coins (does nothing)")
        print(f"- Get a Penalty for 50 coins (does nothing)")
        print(f"{CYAN}======================================{RESET}\n")

    def award_coins(self, reason: str):
        """
        Award coins to the user based on achievement
        
        Args:
            reason (str): Reason for awarding coins ('task_completion' or 'chapter_completion')
        """
        if reason in self.coin_rewards:
            coins_earned = self.coin_rewards[reason]
            self.user_coins += coins_earned
            print(f"{GREEN}+{coins_earned} coins earned for {reason.replace('_', ' ')}!{RESET}")
            self.save_progress()  # Save updated coin balance
            self.display_coin_status()

    def purchase_full_script(self) -> bool:
        try:
            cost = self.coin_costs["full_script"]
            
            if self.user_coins >= cost:
                self.user_coins -= cost
                self.script_detail_level = "Give the whole script"
                self.metrics_logger.log_coin_transaction(-cost, "script_purchase", self.user_coins)
                self.metrics_logger.log_script_purchase()
                print(f"{GREEN}Purchase successful! {cost} coins deducted.{RESET}")
                print(f"{BLUE}You will now receive the complete script implementation.{RESET}")
                self.save_progress()
                return True
            else:
                print(f"{RED}Not enough coins! You need {cost} coins but have {self.user_coins}.{RESET}")
                return False
        except Exception as e:
            self.metrics_logger.log_error(f"Script purchase error: {str(e)}")
            raise

    def award_coins(self, reason: str):
        try:
            if reason in self.coin_rewards:
                coins_earned = self.coin_rewards[reason]
                self.user_coins += coins_earned
                self.metrics_logger.log_coin_transaction(coins_earned, reason, self.user_coins)
                print(f"{GREEN}+{coins_earned} coins earned for {reason.replace('_', ' ')}!{RESET}")
                self.save_progress()
                self.display_coin_status()
        except Exception as e:
            self.metrics_logger.log_error(f"Coin award error: {str(e)}")
            raise


    def check_script_task(self, task: Dict) -> bool:
        """
        Check if a task involves scripting
        
        Args:
            task (Dict): Task details
        
        Returns:
            bool: True if the task involves scripting, False otherwise
        """
        # Keywords that indicate a scripting task
        script_keywords = [
            'script', 'coding', 'programming', 'C#', 'csharp', 
            'function', 'method', 'class', 'component'
        ]
        
        # Check task description and explanation
        task_text = (task.get('description', '') + ' ' + 
                    task.get('explanation', '')).lower()
        
        # Check for script keywords
        for keyword in script_keywords:
            if keyword.lower() in task_text:
                return True
        
        # Check if expected object contains scripting components
        expected_object = task.get('expected_object', {})
        components = expected_object.get('components', [])
        
        for component in components:
            if 'script' in component.lower() or 'behavior' in component.lower():
                return True
        
        return False

    def get_existing_scripts(self) -> str:
        """
        Scan the project for existing C# scripts to provide context
        
        Returns:
            str: Formatted string of existing scripts and their content
        """
        scripts_content = ""
        script_count = 0
        
        # Path to scripts folder
        scripts_path = os.path.join(self.project_path, 'Assets', 'Scripts')
        
        if not os.path.exists(scripts_path):
            return "No existing scripts found."
        
        # Collect script files
        for root, _, files in os.walk(scripts_path):
            for file in files:
                if file.endswith('.cs'):
                    script_path = os.path.join(root, file)
                    try:
                        with open(script_path, 'r', encoding='utf-8') as script_file:
                            content = script_file.read()
                            scripts_content += f"\n--- {file} ---\n"
                            scripts_content += content
                            scripts_content += "\n\n"
                            script_count += 1
                    except Exception as e:
                        scripts_content += f"\nError reading {file}: {e}\n"
        
        if script_count == 0:
            return "No existing scripts found."
        
        return scripts_content




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
        Save current learning progress to a JSON file, including coins and script detail level
        """
        progress_data = {
            'learning_path': self.learning_path,
            'current_chapter_index': self.current_chapter_index,
            'current_task_index': self.current_task_index,
            'user_coins': self.user_coins,
            'script_detail_level': self.script_detail_level
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
                required_keys = ['learning_path', 'current_chapter_index', 'current_task_index']
                if all(key in progress_data for key in required_keys):
                    # Load coin balance and script detail level if available
                    if 'user_coins' in progress_data:
                        self.user_coins = progress_data['user_coins']
                    if 'script_detail_level' in progress_data:
                        self.script_detail_level = progress_data['script_detail_level']
                    
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
        try:
            sprite_structure = self.get_directory_structure()
            sprite_details = self.prepare_sprite_details_for_gemini(sprite_structure)
            
            game_concept = f"""
        Game Concept for Dyslexia Support Educational Game
        
        Game Design Document Insights:
        {self.gdd_content[:1000]}
        
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
            prompt += """
        Additional Requirements:
        1. Include scripting tasks that involve creating C# scripts for game functionality
        2. Distribute scripting tasks evenly across chapters
        3. For scripting tasks, specify the script filename and basic functionality
        4. Each chapter should have at least one scripting task
        5. Script tasks should be properly connected with existing scripts
        6. If the recommended_sprites are empty mention that the user should add sprites and describe them in their names in the recommended_sprites section
        7. For each tasks that require a script add the script (not complete script just a part of it with description so the user can use it himself) add this in the steps section
        """
            
            response = await self.generate_initial(prompt)
            
            def extract_json(text: str) -> Dict:
                json_match = re.search(r'\{.*\}', text, re.DOTALL | re.MULTILINE)
                
                if json_match:
                    try:
                        return json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        try:
                            cleaned_text = text[text.index('{'):text.rindex('}')+1]
                            return json.loads(cleaned_text)
                        except (ValueError, json.JSONDecodeError):
                            print(f"{RED}JSON Parsing Error: Unable to extract valid JSON{RESET}")
                            print(f"{BLUE}Raw Response:{RESET}\n{response}")
                            raise ValueError("Invalid JSON structure")
                
                raise ValueError("No valid JSON found in the response")
            
            learning_path = extract_json(response)
            return learning_path
        
        except Exception as e:
            self.metrics_logger.log_error(f"Learning path generation error: {str(e)}")
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


    async def show_coin_options_menu(self, current_task: Dict) -> bool:
        """
        Show coin options menu and return True if full script was purchased
        """
        while True:
            print(f"\n{CYAN}=========== COIN MENU ==========={RESET}")
            print(f"{GREEN}You have {self.user_coins} coins{RESET}")
            print(f"{BLUE}Available options:{RESET}")
            print(f"1. Purchase full script implementation for {self.coin_costs['full_script']} coins")
            print(f"2. Get a Bonus for 60 coins (does nothing)")
            print(f"3. Get a Penalty for 50 coins (does nothing)")
            print(f"4. Continue with current script detail level ({self.script_detail_level})")
            print(f"{CYAN}======================================{RESET}\n")
            
            choice = input(f"{CYAN}Enter your choice (1-4): {RESET}").strip()
            
            if choice == '1':
                if self.user_coins >= self.coin_costs['full_script']:
                    self.user_coins -= self.coin_costs['full_script']
                    self.script_detail_level = "Give the whole script"
                    self.metrics_logger.log_coin_transaction(
                        -self.coin_costs['full_script'],
                        "script_purchase", 
                        self.user_coins
                    )
                    self.metrics_logger.log_script_purchase()
                    self.save_progress()
                    return True  # Indicate full script was purchased
                else:
                    print(f"{RED}Not enough coins! You need {self.coin_costs['full_script']} coins but have {self.user_coins}.{RESET}")
            elif choice == '2':
                if self.user_coins >= 60:
                    self.user_coins -= 60
                    print(f"{YELLOW}You spent 60 coins for a Bonus! (This does nothing){RESET}")
                    self.save_progress()
                else:
                    print(f"{RED}Not enough coins! You need 60 coins but have {self.user_coins}.{RESET}")
            elif choice == '3':
                if self.user_coins >= 50:
                    self.user_coins -= 50
                    print(f"{YELLOW}You spent 50 coins for a Penalty! (This does nothing){RESET}")
                    self.save_progress()
                else:
                    print(f"{RED}Not enough coins! You need 50 coins but have {self.user_coins}.{RESET}")
            elif choice == '4':
                return False  # No purchase made
            else:
                print(f"{RED}Invalid choice. Please enter a number between 1 and 4.{RESET}")


    def wait_for_command(self, command_event, current_task):
        """
        Listen for user commands while waiting for scene changes
        """
        try:
            print(f"{CYAN}Type 'menu' at any time to access coin options.{RESET}")
            
            # Windows-compatible input checking
            while not self._scene_change_flag.is_set() and not command_event.is_set():
                if msvcrt.kbhit():  # Check if a key was pressed
                    key = msvcrt.getch().decode('utf-8')
                    if key == '\r':  # Enter key
                        user_input = input()  # Now get the full input line
                        if user_input.lower() == 'menu':
                            print(f"{CYAN}Opening coin options menu...{RESET}")
                            command_event.set()
                            return
                    
                time.sleep(0.1)  # Small delay to prevent high CPU usage
                
        except Exception as e:
            self.metrics_logger.log_error(f"Command input error: {str(e)}")
            print(f"{RED}Command input error: {e}{RESET}")


    async def validate_task_completion(self, current_task: Dict) -> bool:
        """
        Validate task completion using scene analysis and Gemini AI
        Handles coin purchases and script regeneration with proper user feedback
        """
        try:
            current_chapter = self.learning_path['chapters'][self.current_chapter_index]
            
            # Log validation attempt
            self.metrics_logger.log_validation_attempt(
                current_chapter['number'],
                current_task['number']
            )
            
            # Check if this is a scripting task
            is_script_task = self.check_script_task(current_task)
            
            if is_script_task:
                # Show scripting options BEFORE monitoring begins
                print(f"\n{CYAN}=== SCRIPTING TASK ==={RESET}")
                print(f"Current detail level: {self.script_detail_level}")
                print(f"Your coins: {self.user_coins} (Need {self.coin_costs['full_script']} for full script)")
                
                # Only offer purchase if not already at full detail
                if self.script_detail_level != "Give the whole script":
                    choice = input(f"{CYAN}Purchase full script now? (y/n): {RESET}").strip().lower()
                    if choice == 'y':
                        if self.user_coins >= self.coin_costs['full_script']:
                            self.user_coins -= self.coin_costs['full_script']
                            self.script_detail_level = "Give the whole script"
                            self.metrics_logger.log_coin_transaction(
                                -self.coin_costs['full_script'],
                                "script_purchase",
                                self.user_coins
                            )
                            self.metrics_logger.log_script_purchase()
                            print(f"{GREEN}Full script purchased!{RESET}")
                        else:
                            print(f"{RED}Not enough coins! Continuing with basic script.{RESET}")
                
                # Generate and show script based on current detail level
                script_content = await self.generate_script_content(current_task)
                print(f"\n{BLUE}=== SCRIPT CONTENT ==={RESET}")
                print(script_content)
                print(f"{BLUE}====================={RESET}")
                print(f"\n{CYAN}Implement this script in your Unity project{RESET}")
                input(f"{CYAN}Press Enter when ready to continue...{RESET}")
            
            # Now begin scene monitoring
            print(f"\n{GREEN}=== TASK VALIDATION ==={RESET}")
            print(f"Validating: {current_task['description']}")
            print(f"{CYAN}I'll check your changes when you save the scene{RESET}")
            print(f"{YELLOW}Type 'menu' at any time for options{RESET}")
            
            # Reset scene change flag
            self._scene_change_flag.clear()
            
            # Initial scene analysis
            scene_analysis = comprehensive_scene_analysis(self.project_path)
            self.scene_analysis_count += 1
            self.metrics_logger.log_scene_analysis()
            
            # Check if task is already completed
            pre_existing_prompt = f"""
            Analyze this Unity scene for pre-existing task objects:
            
            Scene Analysis:
            {json.dumps(scene_analysis, indent=2)}
            
            Task Requirements:
            {json.dumps(current_task, indent=2)}
            
            Respond ONLY with 'pre-existing' if all requirements are met exactly,
            or 'not-created' if anything is missing.
            """
            
            pre_existing_response = await self.generate_initial(pre_existing_prompt)
            if 'pre-existing' in pre_existing_response.lower():
                print(f"{GREEN}✓ Task appears already completed!{RESET}")
                confirm = input(f"{CYAN}Confirm completion? (y/n): {RESET}").strip().lower()
                if confirm == 'y':
                    self.metrics_logger.log_task_completion(
                        current_chapter['number'],
                        current_task['number'],
                        True
                    )
                    self.save_progress()
                    return True
            
            # Main monitoring loop
            start_time = time.time()
            timeout = 300  # 5 minute timeout
            
            while True:
                # Check for scene changes
                if self._scene_change_flag.is_set():
                    print(f"{GREEN}Scene change detected! Validating...{RESET}")
                    break
                    
                # Check for timeout
                if time.time() - start_time > timeout:
                    print(f"{YELLOW}Validation timeout. Try again.{RESET}")
                    return False
                    
                # Non-blocking menu check
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8', 'ignore')
                    if key == '\r':  # Enter key
                        cmd = input().strip().lower()
                        if cmd == 'menu':
                            print(f"{CYAN}Opening coin options...{RESET}")
                            purchased_full_script = await self.show_coin_options_menu(current_task)
                            
                            if purchased_full_script:
                                # Regenerate and show full script if purchased
                                print(f"{GREEN}Regenerating script with full implementation...{RESET}")
                                script_content = await self.generate_script_content(current_task)
                                print(f"\n{BLUE}=== FULL SCRIPT IMPLEMENTATION ==={RESET}")
                                print(script_content)
                                print(f"{BLUE}=================================={RESET}")
                                input(f"{CYAN}Press Enter when ready to continue validation...{RESET}")
                            
                            print(f"{CYAN}Resuming validation...{RESET}")
                            # Reset timeout when returning from menu
                            start_time = time.time()
                
                await asyncio.sleep(0.5)
            
            # Perform validation after scene change
            validation_prompt = f"""
            Validate this Unity scene against task requirements:
            
            Scene Analysis:
            {json.dumps(comprehensive_scene_analysis(self.project_path), indent=2)}
            
            Task Requirements:
            {json.dumps(current_task, indent=2)}
            
            Respond with JSON containing:
            {{
                "completed": boolean,
                "feedback": "detailed explanation",
                "missing_components": [list of missing items]
            }}
            """
            
            validation_response = await self.generate_initial(validation_prompt)
            
            try:
                validation_result = json.loads(re.search(r'\{.*\}', validation_response, re.DOTALL).group(0))
                print(f"\n{BLUE}Validation Result:{RESET}")
                print(validation_result.get("feedback", "No feedback provided"))
                
                if validation_result.get("completed", False):
                    self.metrics_logger.log_task_completion(
                        current_chapter['number'],
                        current_task['number'],
                        True
                    )
                    self.award_coins('task_completion')
                    self.save_progress()
                    return True
                
                return False
                
            except Exception as e:
                print(f"{RED}Validation error: {e}{RESET}")
                return False

        except Exception as e:
            self.metrics_logger.log_error(f"Task validation failed: {str(e)}")
            print(f"{RED}Error during validation: {e}{RESET}")
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
        Present the current task to the user with clear instructions
        """
        if not self.learning_path or self.current_chapter_index >= len(self.learning_path['chapters']):
            print(f"{GREEN}=== TUTORIAL COMPLETE ==={RESET}")
            print(f"You've finished all chapters!")
            return False
        
        current_chapter = self.learning_path['chapters'][self.current_chapter_index]
        
        if self.current_task_index >= len(current_chapter['tasks']):
            # Chapter complete
            self.award_coins('chapter_completion')
            self.current_chapter_index += 1
            self.current_task_index = 0
            return await self.present_current_task()
        
        current_task = current_chapter['tasks'][self.current_task_index]
        
        # Clear screen and show header
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"{CYAN}=== UNITY LEARNING TUTOR ==={RESET}")
        self.display_coin_status()
        
        # Show task info
        print(f"\n{BLUE}CHAPTER {current_chapter['number']}: {current_chapter['title']}{RESET}")
        print(f"{GREEN}TASK {current_task['number']}: {current_task['description']}{RESET}")
        
        # Task details
        print(f"\n{YELLOW}Explanation:{RESET}")
        print(textwrap.fill(current_task.get('explanation', 'No additional explanation'), width=80))
        
        print(f"\n{CYAN}Steps to Complete:{RESET}")
        for i, step in enumerate(current_task.get('steps', []), 1):
            print(f"{i}. {step}")
        
        # Special handling for scripting tasks
        if self.check_script_task(current_task):
            print(f"\n{YELLOW}NOTE: This task involves scripting!{RESET}")
            print(f"Current script detail level: {self.script_detail_level}")
        
        print(f"\n{GREEN}When ready, implement these changes in Unity{RESET}")
        print(f"The tutor will validate your work when you save the scene")
        return True

    async def run_learning_path(self):
        try:
            start_mode = self.choose_start_mode()
            
            if start_mode == 'new' or not self.learning_path:
                self.learning_path = await self.generate_learning_path()
                self.current_chapter_index = 0
                self.current_task_index = 0
            
            self.setup_watchdog()
            self.metrics_logger.metrics['learning_path'] = self.learning_path
            
            while await self.present_current_task():
                current_chapter = self.learning_path['chapters'][self.current_chapter_index]
                current_task = current_chapter['tasks'][self.current_task_index]
                
                if self.current_task_index == 0:
                    self.metrics_logger.log_chapter_start(
                        current_chapter['number'],
                        current_chapter.get('title', 'Untitled Chapter')
                    )
                
                self.metrics_logger.log_task_start(
                    current_chapter['number'],
                    current_task['number'],
                    current_task.get('description', 'Untitled Task')
                )
                
                task_completed = await self.validate_task_completion(current_task)
                
                if task_completed:
                    self.metrics_logger.log_task_completion(
                        current_chapter['number'],
                        current_task['number'],
                        True
                    )
                    
                    if self.current_task_index == len(current_chapter['tasks']) - 1:
                        self.metrics_logger.log_chapter_completion(current_chapter['number'])
                    
                    print(f"{GREEN}Task completed successfully!{RESET}")
                    print(f"{CYAN}Scene analysis performed {self.scene_analysis_count} times.{RESET}")
                    self.award_coins('task_completion')
                    input(f"{CYAN}Press Enter to continue to the next task...{RESET}")
                    self.current_task_index += 1
                    self.save_progress()
                else:
                    print(f"{YELLOW}Please complete the task and save your scene.{RESET}")
                    await asyncio.sleep(3)
        
        except Exception as e:
            self.metrics_logger.log_error(f"Learning path error: {str(e)}")
            traceback.print_exc()
        finally:
            self.metrics_logger.log_session_end()
            self.cleanup_watchdog()

    def command_listener(self):
        """
        Listen for user commands during script tasks
        """
        try:
            user_input = input(f"{CYAN}Enter 'buy-script' to purchase full script, 'bonus' for a Bonus (60 coins), 'penalty' for a Penalty (50 coins), or press Enter to continue: {RESET}").strip()
            
            if user_input.lower() == 'buy-script':
                purchased = self.purchase_full_script()
                
                if purchased:
                    # Force redraw of current task to show updated script information
                    print(f"{GREEN}Script detail level updated to: {self.script_detail_level}{RESET}")
                    print(f"{GREEN}The next time you view a script, you'll get the full implementation.{RESET}")
            elif user_input.lower() == 'bonus':
                if self.user_coins >= 60:
                    self.user_coins -= 60
                    print(f"{YELLOW}You spent 60 coins for a Bonus! (This does nothing){RESET}")
                    self.save_progress()  # Save updated coin balance
                    self.display_coin_status()
                else:
                    print(f"{RED}Not enough coins! You need 60 coins but have {self.user_coins}.{RESET}")
            elif user_input.lower() == 'penalty':
                if self.user_coins >= 50:
                    self.user_coins -= 50
                    print(f"{YELLOW}You spent 50 coins for a Penalty! (This does nothing){RESET}")
                    self.save_progress()  # Save updated coin balance
                    self.display_coin_status()
                else:
                    print(f"{RED}Not enough coins! You need 50 coins but have {self.user_coins}.{RESET}")
        except Exception as e:
            print(f"{RED}Command input error: {e}{RESET}")


    async def generate_script_content(self, task: Dict) -> str:
        try:
            existing_scripts = self.get_existing_scripts()
            
            prompt = f"""
        Task: {task['description']}
        
        Task Explanation: {task.get('explanation', 'No additional explanation provided.')}
        
        Expected Object:
        {json.dumps(task.get('expected_object', {}), indent=2)}
        
        Detail Level: {self.script_detail_level}
        
        Existing Scripts Context:
        {existing_scripts}
        
        Instructions:
        1. Generate Unity C# script content for this task
        2. Make sure the script works with existing scripts
        3. Follow the detail level requested
        4. If detail level is "Give only the functions and description of each one", 
        provide a skeleton with function signatures and comments
        5. If detail level is "Give the whole script", provide complete implementation
        6. Ensure script includes proper namespace, imports, and class structure
        7. Consider integration with the dyslexia game context
        
        Format the output as a Unity C# script ready to be copied into a .cs file.
        """
            
            script_response = await self.generate_initial(prompt)
            code_block = re.search(r'```csharp\n(.*?)```', script_response, re.DOTALL)
            
            if code_block:
                return code_block.group(1).strip()
            else:
                return script_response
        
        except Exception as e:
            self.metrics_logger.log_error(f"Script generation error: {str(e)}")
            return f"Error generating script: {e}"


    def setup_watchdog(self):
        try:
            class ProjectWatchdog(FileSystemEventHandler):
                def __init__(self, learning_tutor):
                    self.learning_tutor = learning_tutor
                    self.last_analyzed_time = 0
                
                def on_modified(self, event):
                    if not event.is_directory and event.src_path.endswith('.unity'):
                        current_time = time.time()
                        if current_time - self.last_analyzed_time > 2:
                            self.last_analyzed_time = current_time
                            print(f"{GREEN}Scene saved! Processing changes...{RESET}")
                            self.learning_tutor._scene_change_flag.set()
            
            self.watchdog = ProjectWatchdog(self)
            self.watchdog_observer = Observer()
            self.watchdog_observer.schedule(self.watchdog, self.project_path, recursive=True)
            self.watchdog_observer.start()
        except Exception as e:
            self.metrics_logger.log_error(f"Watchdog setup error: {str(e)}")
            raise

    def cleanup_watchdog(self):
        try:
            if self.watchdog_observer:
                self.watchdog_observer.stop()
                self.watchdog_observer.join()
        except Exception as e:
            self.metrics_logger.log_error(f"Watchdog cleanup error: {str(e)}")
            raise

async def main():
    print(f"{CYAN}=== Unity Learning Tutor with GDD Validation ==={RESET}")
    
    # Select project path via file dialog
    print(f"{BLUE}Please select your Unity project directory...{RESET}")
    project_path = select_project_path()
    if not project_path:
        print(f"{RED}No project directory selected. Exiting.{RESET}")
        return
    
    # Select GDD file via file dialog
    print(f"{BLUE}Please select your Game Design Document file...{RESET}")
    gdd_path = select_gdd_file()
    if not gdd_path:
        print(f"{RED}No GDD file selected. Exiting.{RESET}")
        return
    
    # Extract GDD content
    print(f"{BLUE}Extracting GDD content...{RESET}")
    gdd_content = extract_gdd_content(gdd_path)
    if not gdd_content:
        print(f"{RED}Could not extract content from GDD. Please check the file format.{RESET}")
        return
    
    # Get Gemini API key
    gemini_api_key = input(f"{CYAN}Enter your Gemini API Key: {RESET}").strip()
    if not gemini_api_key:
        print(f"{RED}API key is required. Exiting.{RESET}")
        return
    
    # Configure Gemini API
    print(f"{BLUE}Configuring Gemini API...{RESET}")
    try:
        genai.configure(api_key=gemini_api_key)
        gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Test API key with a simple request
        test_response = gemini_client.generate_content("Hello")
        if not test_response:
            print(f"{RED}API key validation failed. Please check your key.{RESET}")
            return
    except Exception as e:
        print(f"{RED}Error configuring Gemini API: {e}{RESET}")
        return
    
    # Validate GDD
    print(f"{BLUE}Validating Game Design Document using Octalysis Framework...{RESET}")
    print(f"{YELLOW}This may take a minute or two. Please wait...{RESET}")
    
    try:
        validation_results = validate_gdd_with_octalysis(gemini_client, gdd_content)
        
        # Save initial validation report
        report_path = save_validation_report(validation_results, project_path)
        
        # Display validation summary
        print(f"\n{GREEN}=== GDD Validation Complete ==={RESET}")
        print(f"{BLUE}Summary: {validation_results['summary']}{RESET}")
        print(f"{BLUE}Overall Score: {validation_results['overall_score']}/10{RESET}")
        
        print(f"\n{GREEN}Top Recommendations:{RESET}")
        for i, rec in enumerate(validation_results['top_recommendations'][:3], 1):
            print(f"{i}. {rec}")
        
        print(f"\n{CYAN}A detailed report has been saved to: {report_path}{RESET}")
        
        # Refinement loop
        while True:
            choice = input(f"\n{CYAN}Would you like to: (1) Proceed with learning path, (2) Refine GDD, or (3) Exit? [1/2/3]: {RESET}").strip().lower()
            
            if choice in ['1', 'proceed']:
                break  # Exit loop and continue to learning path
                
            elif choice in ['2', 'refine']:
                # Get user feedback for refinement
                print(f"{BLUE}Please provide specific aspects you'd like to improve based on the recommendations:{RESET}")
                user_feedback = input().strip()
                
                print(f"{BLUE}Generating refined GDD suggestions...{RESET}")
                
                # Generate refined GDD suggestions
                refinement_prompt = f"""
                Based on the Octalysis Framework analysis, the original GDD has these issues:
                {validation_results['summary']}
                
                The user wants to improve these specific aspects:
                {user_feedback}
                
                Please provide specific, actionable edits to the GDD that would address these concerns.
                Focus on concrete changes that would improve the game's engagement using the Octalysis Framework.
                
                Format your response as specific sections to add or modify in the GDD.
                """
                
                try:
                    refinement_response = gemini_client.generate_content(refinement_prompt)
                    
                    # Save refinement suggestions to the same report
                    report_path = save_validation_report(
                        validation_results, 
                        project_path,
                        refinement_response.text
                    )
                    
                    # Update the in-memory GDD content
                    gdd_content += "\n\n=== REFINEMENTS ===\n" + refinement_response.text
                    
                    print(f"\n{GREEN}Refinement suggestions have been added to: {report_path}{RESET}")
                    print(f"{BLUE}These suggestions have been incorporated into your learning path.{RESET}")
                    
                except Exception as e:
                    print(f"{RED}Error generating refinement suggestions: {e}{RESET}")
                    
            elif choice in ['3', 'exit']:
                return  # Exit the program
                
            else:
                print(f"{RED}Invalid choice. Please try again.{RESET}")
    
    except Exception as e:
        print(f"{RED}Error during GDD validation: {e}{RESET}")
        print(f"{YELLOW}Would you like to continue without validation? (yes/no): {RESET}")
        continue_choice = input().strip().lower()
        if continue_choice not in ['yes', 'y']:
            return
    
    # Initialize and run learning tutor with potentially updated gdd_content
    print(f"{BLUE}Initializing Unity Learning Tutor...{RESET}")
    tutor = UnityLearningTutor(gemini_api_key, project_path, gdd_content)
    await tutor.run_learning_path()

if __name__ == "__main__":
    asyncio.run(main())