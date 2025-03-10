import os
from google import genai
from conf import Gemini_key
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

best_practice=r"""
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using UnityEngine.EventSystems;

public class MenuUI : MonoBehaviour
{
    private Canvas menuCanvas;
    private GameObject mainPanel;
    private Camera mainCamera;

    void Awake()
    {
        SetupCamera();
        SetupEventSystem();
        SetupMenu();
    }

    void SetupCamera()
    {
        // Create and setup main camera if it doesn't exist
        if (Camera.main == null)
        {
            GameObject cameraObj = new GameObject("Main Camera");
            mainCamera = cameraObj.AddComponent<Camera>();
            cameraObj.tag = "MainCamera";

            // Configure camera
            mainCamera.clearFlags = CameraClearFlags.SolidColor;
            mainCamera.backgroundColor = new Color(0.7f, 0.9f, 1f); // Light blue background
            mainCamera.orthographic = true;
            mainCamera.orthographicSize = 5;
            mainCamera.transform.position = new Vector3(0, 0, -10);
        }
        else
        {
            mainCamera = Camera.main;
        }
    }

    void SetupEventSystem()
    {
        // Ensure we have an EventSystem
        if (FindObjectOfType<EventSystem>() == null)
        {
            GameObject eventSystem = new GameObject("EventSystem");
            eventSystem.AddComponent<EventSystem>();
            eventSystem.AddComponent<StandaloneInputModule>();
        }
    }

    void SetupMenu()
    {
        // Create canvas
        GameObject canvasObj = new GameObject("MenuCanvas");
        menuCanvas = canvasObj.AddComponent<Canvas>();
        menuCanvas.renderMode = RenderMode.ScreenSpaceOverlay;

        // Add required components
        CanvasScaler scaler = canvasObj.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        scaler.matchWidthOrHeight = 0.5f;

        canvasObj.AddComponent<GraphicRaycaster>();

        // Create main panel
        CreateMainPanel();

        // Ensure this canvas is at the front
        menuCanvas.sortingOrder = 999;
    }

    void CreateMainPanel()
    {
        // Create panel
        mainPanel = new GameObject("MainPanel");
        mainPanel.transform.SetParent(menuCanvas.transform, false);

        // Add background
        Image bgImage = mainPanel.AddComponent<Image>();
        bgImage.color = new Color(0.1f, 0.1f, 0.2f, 0.95f); // Slightly transparent dark blue

        // Make panel fill entire screen
        RectTransform bgRect = bgImage.GetComponent<RectTransform>();
        bgRect.anchorMin = Vector2.zero;
        bgRect.anchorMax = Vector2.one;
        bgRect.offsetMin = Vector2.zero;
        bgRect.offsetMax = Vector2.zero;

        // Create title
        GameObject titleObj = new GameObject("TitleText");
        titleObj.transform.SetParent(mainPanel.transform, false);
        TextMeshProUGUI titleText = titleObj.AddComponent<TextMeshProUGUI>();
        titleText.text = "Animal Spelling Game";
        titleText.fontSize = 72;
        titleText.alignment = TextAlignmentOptions.Center;
        titleText.color = Color.white;

        RectTransform titleRect = titleText.GetComponent<RectTransform>();
        titleRect.anchorMin = new Vector2(0.5f, 0.7f);
        titleRect.anchorMax = new Vector2(0.5f, 0.9f);
        titleRect.sizeDelta = new Vector2(800, 100);
        titleRect.anchoredPosition = Vector2.zero;

        // Create start button
        GameObject startButtonObj = new GameObject("StartButton");
        startButtonObj.transform.SetParent(mainPanel.transform, false);

        Image buttonImage = startButtonObj.AddComponent<Image>();
        buttonImage.color = new Color(0.2f, 0.8f, 0.2f); // Green button
        Button startButton = startButtonObj.AddComponent<Button>();

        // Set button size and position
        RectTransform buttonRect = buttonImage.GetComponent<RectTransform>();
        buttonRect.anchorMin = new Vector2(0.5f, 0.4f);
        buttonRect.anchorMax = new Vector2(0.5f, 0.4f);
        buttonRect.sizeDelta = new Vector2(300, 80);
        buttonRect.anchoredPosition = Vector2.zero;

        // Add button text
        GameObject buttonTextObj = new GameObject("ButtonText");
        buttonTextObj.transform.SetParent(startButtonObj.transform, false);
        TextMeshProUGUI buttonText = buttonTextObj.AddComponent<TextMeshProUGUI>();
        buttonText.text = "Start Game";
        buttonText.fontSize = 36;
        buttonText.alignment = TextAlignmentOptions.Center;
        buttonText.color = Color.white;

        // Set text to fill button
        RectTransform buttonTextRect = buttonText.GetComponent<RectTransform>();
        buttonTextRect.anchorMin = Vector2.zero;
        buttonTextRect.anchorMax = Vector2.one;
        buttonTextRect.offsetMin = Vector2.zero;
        buttonTextRect.offsetMax = Vector2.zero;

        // Add button functionality
        startButton.onClick.AddListener(() => {
            StartGame();
        });
    }

    void StartGame()
    {
        // Hide menu
        menuCanvas.gameObject.SetActive(false);

        // Create GameUI if it doesn't exist
        if (FindObjectOfType<GameUI>() == null)
        {
            GameObject gameUIObj = new GameObject("GameUI");
            gameUIObj.AddComponent<GameUI>();
        }
    }
}


---------------------------------------------------------------------------------------------------------------------
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using TMPro;
using UnityEngine.EventSystems;

public class GameUI : MonoBehaviour
{
    private GameObject restartPanel;
    private GameObject winPanel;
    private GameUI gameUI;
    private Canvas overlayCanvas;

    void Awake()
    {
        // First, ensure we have an EventSystem
        if (FindObjectOfType<EventSystem>() == null)
        {
            GameObject eventSystem = new GameObject("EventSystem");
            eventSystem.AddComponent<EventSystem>();
            eventSystem.AddComponent<StandaloneInputModule>();
            Debug.Log("Created new EventSystem");
        }

        gameUI = FindObjectOfType<GameUI>();
        if (gameUI == null)
        {
            Debug.LogError("GameUI not found!");
            return;
        }

        // Create canvas
        GameObject canvasObj = new GameObject("UICanvas");
        overlayCanvas = canvasObj.AddComponent<Canvas>();
        overlayCanvas.renderMode = RenderMode.ScreenSpaceOverlay;
        overlayCanvas.sortingOrder = 999;

        // Make sure to add a GraphicRaycaster
        GraphicRaycaster raycaster = canvasObj.AddComponent<GraphicRaycaster>();

        // Add CanvasScaler
        CanvasScaler scaler = canvasObj.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);

        CreatePanels();
    }

    private void CreatePanels()
    {
        // Create Restart Panel
        restartPanel = CreatePanel("RestartPanel", "Game Over!\nTry Again?", true);
        restartPanel.SetActive(false);

        // Create Win Panel
        winPanel = CreatePanel("WinPanel", "You Win!", false);
        winPanel.SetActive(false);
    }

    private GameObject CreatePanel(string name, string message, bool isRestartPanel)
    {
        // Create panel
        GameObject panel = new GameObject(name);
        panel.transform.SetParent(overlayCanvas.transform, false);

        // Add background
        Image bgImage = panel.AddComponent<Image>();
        bgImage.color = new Color(0, 0, 0, 0.8f);
        RectTransform bgRect = bgImage.GetComponent<RectTransform>();
        bgRect.anchorMin = Vector2.zero;
        bgRect.anchorMax = Vector2.one;
        bgRect.sizeDelta = Vector2.zero;

        // Add text
        GameObject textObj = new GameObject("Text");
        textObj.transform.SetParent(panel.transform, false);
        TextMeshProUGUI tmp = textObj.AddComponent<TextMeshProUGUI>();
        tmp.text = message;
        tmp.fontSize = 50;
        tmp.alignment = TextAlignmentOptions.Center;
        tmp.color = Color.white;
        RectTransform textRect = tmp.GetComponent<RectTransform>();
        textRect.anchorMin = new Vector2(0.5f, 0.6f);
        textRect.anchorMax = new Vector2(0.5f, 0.8f);
        textRect.sizeDelta = new Vector2(400, 200);
        textRect.anchoredPosition = Vector2.zero;

        // Add button
        GameObject buttonObj = new GameObject("Button");
        buttonObj.transform.SetParent(panel.transform, false);

        Button button = buttonObj.AddComponent<Button>();
        Image buttonImage = buttonObj.AddComponent<Image>();
        buttonImage.color = new Color(0.2f, 0.8f, 0.2f);

        RectTransform buttonRect = buttonImage.GetComponent<RectTransform>();
        buttonRect.anchorMin = new Vector2(0.5f, 0.3f);
        buttonRect.anchorMax = new Vector2(0.5f, 0.3f);
        buttonRect.sizeDelta = new Vector2(200, 60);
        buttonRect.anchoredPosition = Vector2.zero;

        // Add button text
        GameObject buttonTextObj = new GameObject("ButtonText");
        buttonTextObj.transform.SetParent(buttonObj.transform, false);
        TextMeshProUGUI buttonText = buttonTextObj.AddComponent<TextMeshProUGUI>();
        buttonText.text = isRestartPanel ? "Restart" : "Continue";
        buttonText.fontSize = 30;
        buttonText.alignment = TextAlignmentOptions.Center;
        buttonText.color = Color.white;

        RectTransform buttonTextRect = buttonText.GetComponent<RectTransform>();
        buttonTextRect.anchorMin = Vector2.zero;
        buttonTextRect.anchorMax = Vector2.one;
        buttonTextRect.sizeDelta = Vector2.zero;

        // Add button functionality
        button.onClick.AddListener(() => {
            Debug.Log($"Button clicked in {name}!");
            if (isRestartPanel)
            {
                Debug.Log("Attempting to restart level");
                gameUI.RestartLevel();
                HideRestartPanel();
            }
            else
            {
                Debug.Log("Attempting to go to next level");
                gameUI.NextLevel();
                HideWinPanel();
            }
        });

        return panel;
    }

    public void ShowRestartPanel()
    {
        if (restartPanel != null)
        {
            Time.timeScale = 0f;
            restartPanel.SetActive(true);
        }
    }

    public void HideRestartPanel()
    {
        if (restartPanel != null)
        {
            Time.timeScale = 1f;
            restartPanel.SetActive(false);
        }
    }

    public void ShowWinPanel()
    {
        if (winPanel != null)
        {
            Time.timeScale = 0f;
            winPanel.SetActive(true);
        }
    }

    public void HideWinPanel()
    {
        if (winPanel != null)
        {
            Time.timeScale = 1f;
            winPanel.SetActive(false);
        }
    }

    void OnDestroy()
    {
        Time.timeScale = 1f;
    }
}
"""

########################## GAme UI Agent
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

class GameUIAgent(DevelopmentAgent):
    def __init__(self):
        super().__init__("Game UI Agent", ORANGE)
        
    async def get_gemini_response(self):
        """Generate initial scripts for UI, LetterBehaviour, and GameLauncher"""
        
        # Get context data
        ui_suggestion = read_ui_suggestion()
        code3 = read_code("Game_UI.md")
        prompt = fr"""
You are a Game developer with the following tasks:
1- Create the Script for the game that would create GameObjects, Cameras, Canvas, Groundes, Players ... etc automatically.
2- The script should be based on the Brainstorming results and the UI existing assets.
3- You need to work only on the Files [GameUI.cs, MenuUI.cs]
The MenuUI class in Unity initializes a menu interface by setting up a camera, an event system, and a UI canvas with a title and a start button that begins the game. The GameUI class creates an overlay UI with restart and win panels, ensuring that necessary UI components like event systems, canvases, and buttons are properly instantiated. Both classes dynamically generate UI elements, manage user interactions, and control scene transitions for a smooth gameplay experience.
4- Create and integrate a gamification system including:
   - Score tracking and display
   - Lives/Hearts system
   - Achievement notifications 
   - High score display
   - Visual feedback for player actions
5- Here is an example of the script to be inspired from: Edit, Modify, add functions or delete others based on the needs of the game:
{best_practice}
The GameUI file:
{code3}
6- Here is the UI assets:
{ui_suggestion}
7- Provide **structured output** with clear file boundaries:
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
    You are the Game UI Agent responsible for Unity game setup.

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
        
        print(f"{self.color}Game UI Agent processing feedback...{RESET}")
        response = await asyncio.to_thread(lambda: chat.send_message(prompt))
        response_text = response.text.strip()
        
        # Extract summary and script
        summary_match = re.search(r'<SUMMARY>(.*?)</SUMMARY>', response_text, re.DOTALL)
        script_match = re.search(r'<SCRIPT>(.*?)</SCRIPT>', response_text, re.DOTALL)
        
        summary = summary_match.group(1).strip() if summary_match else "No summary provided."
        updated_script = script_match.group(1).strip() if script_match else response_text
        
        # Print the summary
        print(f"{self.color}=== Game UI Change Report ===")
        print(f"{self.color}{summary}{RESET}")
        print(f"{self.color}================================={RESET}")
        
        return updated_script