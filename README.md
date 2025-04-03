# 🚀 AI-Driven Unity Game Development

## 📌 Overview
This project enables the creation or modification of a Unity 3D game entirely through AI agents, eliminating the need for manual Unity development. AI agents handle everything from brainstorming to final deployment.

---

## 🛠 Installation & Setup

### 📋 Prerequisites
- ✅ Python 3.8+
- ✅ Unity 3D Installed
- ✅ Google Gemini API Key (for AI Agents)

### 📂 Setup Instructions

```sh
# Install dependencies:
python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

# Configure API keys:
# Set your Gemini API keys.

# Run the project:
python main.py

# To run the Learning Tutor separately:
cd Agents
python Tutor.py
```

---

## 🤖 AI Agents & Functions

| Agent | Description | Key Functions |
|--------|---------------------------|------------------------------|
| **Learning Tutor Agent** | AI-guided Unity game development tutor | `generate_learning_path()`, `validate_task_completion()`, `present_current_task()` |
| **Brainstorming Agent** | Generates and refines game ideas, processes UI assets. | `read_brainstorm_file()`, `get_directory_structure()`, `get_gemini_ui_suggestion()` |
| **Game Controller Agent** | Manages game logic and player mechanics. | `generate_initial(prompt)`, `handle_feedback(feedback, script)` |
| **Game Manager Agent** | Oversees game flow and state transitions. | `initialize_game()`, `handle_game_state()` |
| **Game UI Agent** | Creates UI elements dynamically from assets. | `get_directory_structure()`, `generate_UI_structure()` |
| **Game Scenes Agent** | Automates scene creation and level setup. | `setup_scene()`, `save_scene_state()` |
| **Game Tester Agent** | Ensures all scripts function correctly. | `analyze_integration()`, `process_error(error_message)` |
| **Code Editor Agent** | Modifies and updates existing Unity scripts. | `process_user_request(request)`, `scan_unity_project()` |

---

## 🎮 Learning Tutor Agent Details

### 📌 Purpose
The Learning Tutor Agent is a specialized AI-driven development assistant focused on guiding users through Unity game development, specifically tailored for creating a Dyslexia Support Educational Game.

### 🚀 Workflow
1. **Initialization**
   - Requires Gemini API Key
   - Specifies Unity Project Path
   - Generates a comprehensive learning path

2. **Interactive Learning Modes**
   - **New Learning Path**: 
     - Generates a step-by-step game development tutorial
     - Creates tasks for each development stage
   - **Continue Previous Progress**: 
     - Loads existing project progress
     - Resumes from last completed task

3. **Task Completion Process**
   - Presents detailed task instructions
   - Monitors scene changes
   - Validates task completion using AI
   - Tracks and saves progress automatically

### 🔍 Key Features
- AI-powered task generation
- Real-time scene monitoring
- Automatic progress tracking
- Gemini AI task validation
- Asyncio-based concurrent processing

### 🎯 Example Workflow
```
# Starting the Learning Tutor
$ python Tutor.py

# Prompts:
> Enter your Gemini API Key: [YOUR_API_KEY]
> Enter the path to your Unity project: /path/to/your/unity/project

# Interactive Modes:
1. Start a New Learning Path
2. Continue Previous Progress
3. Exit

# Sample Task Example:
Chapter 1: Vowel Island Setup
Task 1: Create Vowel Island Main Camera
- Open Hierarchy Window
- Right-Click > 2D Object > Camera
- Rename camera to 'VowelIslandCamera'
- Position camera to capture entire Vowel Island scene
```

---

## 🎮 User Interaction & Workflow

### 1️⃣ Starting the Project
- Select an option:
  - **New Game** – AI generates all scripts from scratch.
  - **Edit Game** – Modify an existing Unity project.
- If creating a new game, input an idea or upload a `.docx` file.

### 2️⃣ Game Generation & Refinement
- AI generates scripts, UI, and mechanics.
- Users review and provide feedback.

### 3️⃣ Testing & Debugging
- AI detects and fixes inconsistencies.
- Unity errors are processed iteratively.



---

## 📈 Development Workflow

1️⃣ **Concept Generation** - Brainstorming Agent formulates ideas.  
2️⃣ **Script Development** - Game Controller & Manager generate mechanics.  
3️⃣ **Scene Setup** - Scenes Agent structures game levels.  
4️⃣ **Testing & Debugging** - Game Tester checks functionality.  
5️⃣ **Code Refinement** - Code Editor modifies scripts. 