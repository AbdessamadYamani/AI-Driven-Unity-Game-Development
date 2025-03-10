import os
from google import genai
from conf import Gemini_key 
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


Exemple=r"""using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEditor;
using UnityEditor.SceneManagement;
using System.Linq;

public class AutoSceneSetup
{
    [InitializeOnLoadMethod]
    public static void Initialize()
    {
        // Only add the update callback if we're not in play mode
        if (!EditorApplication.isPlayingOrWillChangePlaymode)
        {
            EditorApplication.update += OnEditorUpdate;
        }
    }

    static void OnEditorUpdate()
    {
        // Only run once
        EditorApplication.update -= OnEditorUpdate;

        // Check if we're in play mode
        if (EditorApplication.isPlayingOrWillChangePlaymode)
        {
            return;
        }

        try
        {
            // Setup required tags
            SetupTags();

            // Create new scene
            Scene newScene;

            // Use the appropriate scene creation method
            if (Application.isPlaying)
            {
                newScene = SceneScenes.CreateScene("AnimalSpellingGame");
            }
            else
            {
                newScene = EditorSceneScenes.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            }

            // Create Scenes object and add GameScenes script
            GameObject ScenesObject = new GameObject("GameScenes");
            ScenesObject.AddComponent<GameScenes>();

            // Save the scene only if we're in edit mode
            if (!Application.isPlaying)
            {
                string scenePath = "Assets/AnimalSpellingGame.unity";
                EditorSceneScenes.SaveScene(newScene, scenePath);
                Debug.Log("Scene setup completed successfully!");
            }
        }
        catch (System.Exception e)
        {
            Debug.LogError($"Failed to set up scene: {e.Message}");
        }
    }

    static void SetupTags()
    {
        // Get the asset containing the tags
        SerializedObject tagScenes = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagScenes.asset")[0]);
        SerializedProperty tagsProp = tagScenes.FindProperty("tags");

        // List of required tags
        string[] requiredTags = new string[] { "Ground", "Player" };

        // Add each required tag if it doesn't exist
        foreach (string tag in requiredTags)
        {
            bool found = false;
            for (int i = 0; i < tagsProp.arraySize; i++)
            {
                SerializedProperty t = tagsProp.GetArrayElementAtIndex(i);
                if (t.stringValue.Equals(tag)) { found = true; break; }
            }

            // Add the tag if it's not present
            if (!found)
            {
                tagsProp.InsertArrayElementAtIndex(tagsProp.arraySize);
                SerializedProperty newTag = tagsProp.GetArrayElementAtIndex(tagsProp.arraySize - 1);
                newTag.stringValue = tag;
            }
        }

        // Save the changes
        tagScenes.ApplyModifiedProperties();
        Debug.Log("Tags setup completed successfully!");
    }
}

// Custom menu item to manually trigger setup
public class SetupMenu
{
    [MenuItem("Game/Setup Animal Spelling Game")]
    static void SetupGame()
    {
        if (!EditorApplication.isPlayingOrWillChangePlaymode)
        {
            AutoSceneSetup.Initialize();
        }
        else
        {
            Debug.LogWarning("Cannot setup scene during play mode. Please exit play mode first.");
        }
    }
}

"""

########## Game Scene agent
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
def read_ui_suggestion():
    """
    Reads the content of brainstorm.md file.
    
    Returns:
        str: Content of the brainstorm.md file
    """
    try:
        with open(r'UI_suggestion.md', 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print("Warning: UI_suggestion.md file not found. Using empty string.")
        return ""
def read_gamification():
    """
    Reads the content of brainstorm.md file.
    
    Returns:
        str: Content of the brainstorm.md file
    """
    try:
        with open('gamification_system.md', 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print("Warning: UI_suggestion.md file not found. Using empty string.")
        return ""    
def read_code(file_name):
    """
    Reads the content of brainstorm.md file.
    
    Returns:
        str: Content of the brainstorm.md file
    """
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print("Warning: UI_suggestion.md file not found. Using empty string.")
        return ""  




from agent_base import DevelopmentAgent
import asyncio,re
ORANGE="\033[93m"
RESET = "\033[0m"
ui_suggestion = read_ui_suggestion()
class ScenesAgent(DevelopmentAgent):
    def __init__(self):
        super().__init__("Scenes", ORANGE)
        
    async def get_gemini_response(self):
        """Generate initial scripts for PlayerController, LetterBehaviour, and GameLauncher"""
        
        # Get context data
        
        code = read_code("Game_Controller.md")
        code2 = read_code("UIFiles.md")
        code3 = read_code("Game_Scenes.md")
        prompt = fr"""
You are a Game developer with the following tasks:
1- Create the Script for the game that would create GameObjects, Cameras, Canvas, Groundes, Players ... etc automatically.
2- The script should be based on the Brainstorming results and the UI existing assets.
3- You need to work only on the File [AutoSceneSetup] that automates the setup of a new scene by ensuring necessary tags ("Ground" and "Player" ...etc) are added, creating a new empty scene, and adding a GameScenes object with a corresponding script. It executes automatically when the editor starts (if not in play mode) and can also be manually triggered from the "Game" menu. If the editor is not in play mode, it saves the newly created scene to "Assets/AnimalSpellingGame.unity", logging any errors encountered during the process.
4- Here is an example of the script to be inspired from: Edit, Modify, add functions or delete others based on the needs of the game:
{Exemple}
5- Here is the UI assets:
{ui_suggestion}
6- Other codes:
{code}
-----------------------------------
{code2}
------------------------------------
{code3}
6- Provide **structured output** with clear file boundaries:
   - Use `### FILE START: [Full file path]` at the beginning of each file from C:\Users\user\My project (2)  (e.g., C:\Users\user\My project (2)\Assets\+foldername).
   - Use `### FILE END` at the end of each file.
    
IMPORTANT CODING GUIDELINES:
1. All scripts must import necessary Unity namespaces (UnityEngine, System.Collections)
2. All MonoBehaviour classes must have proper lifecycle methods (Awake/Start/Update when needed)
3. Always initialize variables before use
4. Check for null references before accessing properties/methods
5. Ensure proper bracing, method structure, and return values
6. When referencing other scripts, use GetComponent safely
7. Balance all opening and closing braces
8. Ensure inheritance and interfaces are properly implemented
9. Use forward declarations when referencing scripts that haven't been defined yet

IMPORTANT: The most important thing is that the goal is to create a whole game using only AND ONLY script the user should not interact with the GUI , create gameObjects ..etc , 100% Should be create only from script
    """
        
        return await self.generate_initial(prompt)
    
    async def handle_feedback(self, feedback, current_script):
        """Process feedback from the tester and update the script accordingly"""
        client = genai.Client(api_key=Gemini_key)
        chat = client.chats.create(model='gemini-2.0-flash-thinking-exp')
        
        prompt = f"""
    You are the Game Scenes Agent responsible for Unity game setup.

    The Tester has identified these issues in your script:

    {feedback}

    Your current script:
    {current_script}

            Fix each issue mentioned and provide your COMPLETE UPDATED SCRIPT with all corrections.and do not forget to Maintain the same file structure with ### FILE START and ### FILE END markers
When you update a fscript give the whole code for all script corrected and not only the part you corrected
Make sure to remove the ``` from your code 

    Additionally, provide a brief summary of the changes you made to address the feedback.
    Format your response as follows:

    <SUMMARY>
    [Your summary of changes and reasoning here]
    </SUMMARY>

    <SCRIPT>
    [Complete updated script here]
    </SCRIPT>
    """
        
        print(f"{self.color}Game Scenes Agent processing feedback...{RESET}")
        response = await asyncio.to_thread(lambda: chat.send_message(prompt))
        response_text = response.text.strip()
        
        # Extract summary and script
        summary_match = re.search(r'<SUMMARY>(.*?)</SUMMARY>', response_text, re.DOTALL)
        script_match = re.search(r'<SCRIPT>(.*?)</SCRIPT>', response_text, re.DOTALL)
        
        summary = summary_match.group(1).strip() if summary_match else "No summary provided."
        updated_script = script_match.group(1).strip() if script_match else response_text
        
        # Print the summary
        print(f"{self.color}=== Game Scenes Change Report ===")
        print(f"{self.color}{summary}{RESET}")
        print(f"{self.color}================================={RESET}")
        
        return updated_script