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
pip install -r requirements.txt

# Configure API keys:
# Set your Gemini API keys.

# Run the project:
python main.py
```

---

## 🤖 AI Agents & Functions

| Agent | Description | Key Functions |
|--------|---------------------------|------------------------------|
| **Brainstorming Agent** | Generates and refines game ideas, processes UI assets. | `read_brainstorm_file()`, `get_directory_structure()`, `get_gemini_ui_suggestion()` |
| **Game Controller Agent** | Manages game logic and player mechanics. | `generate_initial(prompt)`, `handle_feedback(feedback, script)` |
| **Game Manager Agent** | Oversees game flow and state transitions. | `initialize_game()`, `handle_game_state()` |
| **Game UI Agent** | Creates UI elements dynamically from assets. | `get_directory_structure()`, `generate_UI_structure()` |
| **Game Scenes Agent** | Automates scene creation and level setup. | `setup_scene()`, `save_scene_state()` |
| **Game Tester Agent** | Ensures all scripts function correctly. | `analyze_integration()`, `process_error(error_message)` |
| **Code Editor Agent** | Modifies and updates existing Unity scripts. | `process_user_request(request)`, `scan_unity_project()` |

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

### 4️⃣ Compilation & Deployment
- The game is compiled and exported.
- Users can refine and publish the final version.

---

## 📈 Development Workflow

1️⃣ **Concept Generation** - Brainstorming Agent formulates ideas.  
2️⃣ **Script Development** - Game Controller & Manager generate mechanics.  
3️⃣ **Scene Setup** - Scenes Agent structures game levels.  
4️⃣ **Testing & Debugging** - Game Tester checks functionality.  
5️⃣ **Code Refinement** - Code Editor modifies scripts.  
6️⃣ **Integration & Compilation** - Final debugging and packaging.  
7️⃣ **Deployment** - The completed game is released.  

---


---

