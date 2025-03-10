import os
from google import genai
from conf import Gemini_key
import sys
import asyncio
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_base import DevelopmentAgent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_base import DevelopmentAgent
# Color constants from tester
BLUE = "\033[94m"
RESET = "\033[0m"


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
    



Exemple=r"""
using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;
using System.Linq;
using TMPro;
using AnimalSpellingGame;

public class GameManager : MonoBehaviour
{
    [Header("Game Configuration")]
    [Tooltip("Minimum number of letters to display.")]
    [SerializeField] private int letterCount = 10;

    [Header("UI References")]
    [SerializeField] private TextMeshProUGUI inputDisplay;
    [SerializeField] private Image animalImage;

    // Runtime-generated components
    private GameObject bunnyPlayer;
    private GameObject ground;
    private GameObject[] letterObjects;
    private Camera mainCamera;
    private int wrongLetterLimit = 2;

    // Game state
    private string currentAnimal = "";
    private string currentInput = "";
    private List<string> availableAnimals;
    private List<string> usedAnimals;
    private List<char> availableLetters;
    private HashSet<char> wrongLetters = new HashSet<char>();

    //GameUI
    public GameUI gameUI;
    private void Awake()
    {
        if (FindObjectOfType<GameUI>() == null)
        {
            GameObject gameUIObj = new GameObject("GameUI");
            gameUI = gameUIObj.AddComponent<GameUI>();
        }
        else
        {
            gameUI = FindObjectOfType<GameUI>();
        }

        usedAnimals = new List<string>();
        availableAnimals = new List<string>();
    }
    public void RestartLevel()
    {
        Debug.Log("Restarting level with current animal: " + currentAnimal);

        // Clear current state
        currentInput = "";
        wrongLetters.Clear();

        // Reset bunny position
        if (bunnyPlayer != null)
        {
            bunnyPlayer.transform.position = new Vector3(-8, -3, 0);
        }

        // Destroy existing letter objects and create new ones
        if (letterObjects != null)
        {
            foreach (GameObject letter in letterObjects)
            {
                if (letter != null)
                {
                    Destroy(letter);
                }
            }
        }

        // Update display
        UpdateInputDisplay();

        // Create new letters
        CreateLetterObjects();

        // Resume game
        Time.timeScale = 1f;
    }
    void Start()
    {
        // Check if MenuUI exists - if it does, this GameManager was created by the menu
        MenuUI menuUI = FindObjectOfType<MenuUI>();
        if (menuUI == null)
        {
            // If no MenuUI exists, we're starting the game directly - create one
            GameObject menuObj = new GameObject("MenuUI");
            menuObj.AddComponent<MenuUI>();
            // Don't continue with game setup - we'll wait for menu interaction
            return;
        }

        // Rest of your existing Start() method code here...
        if (gameUI == null)
        {
            Debug.LogError("GameUI not found or failed to initialize!");
            return;
        }

        SetupCamera();
        SetupUI();
        CreateGround();
        CreatePlayer();
        LoadAnimals();
        StartNewRound();
    }

    void LoadAnimals()
    {
        Debug.Log("Loading animals...");
        availableAnimals = new List<string>();
        Object[] animalSprites = Resources.LoadAll("UIs/animals", typeof(Sprite));

        if (animalSprites == null || animalSprites.Length == 0)
        {
            Debug.LogError("No animal sprites found in path: UIs/animals");
            Debug.LogError("Please ensure the following directory exists: Assets/Resources/UIs/animals/");
            availableAnimals.Add("cat");
            availableAnimals.Add("dog");
        }
        else
        {
            for (int i = 0; i < animalSprites.Length; i++)
            {
                Object obj = animalSprites[i];
                string animalName = obj.name.ToLower().Replace(".png", "").Replace("_0", "");
                availableAnimals.Add(animalName);
                Debug.Log($"Loaded animal: {animalName}");
            }
        }
    }
    void SetupCamera()
    {
        Debug.Log("Setting up camera...");
        GameObject cameraObj = new GameObject("Main Camera");
        mainCamera = cameraObj.AddComponent<Camera>();
        cameraObj.tag = "MainCamera";
        mainCamera.orthographic = true;
        mainCamera.orthographicSize = 5;
        mainCamera.backgroundColor = new Color(0.7f, 0.9f, 1f); // Light blue background
        cameraObj.transform.position = new Vector3(0, 0, -10);
        Debug.Log("Camera setup complete");
    }

    void SetupUI()
    {
        Debug.Log("Setting up UI...");
        GameObject canvas = new GameObject("Canvas");
        Canvas canvasComponent = canvas.AddComponent<Canvas>();
        canvasComponent.renderMode = RenderMode.ScreenSpaceOverlay;
        CanvasScaler scaler = canvas.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        canvas.AddComponent<GraphicRaycaster>();

        // Create Animal Display with larger size
        GameObject animalObj = new GameObject("AnimalImage");
        animalObj.transform.SetParent(canvas.transform, false);  // Added false parameter
        animalImage = animalObj.AddComponent<Image>();
        RectTransform animalRect = animalObj.GetComponent<RectTransform>();
        animalRect.anchorMin = new Vector2(0.5f, 1f);
        animalRect.anchorMax = new Vector2(0.5f, 1f);
        animalRect.pivot = new Vector2(0.5f, 1f);
        animalRect.anchoredPosition = new Vector2(0, 5); // Correct position of Animal Image
        animalRect.sizeDelta = new Vector2(150, 150);   // Correct size of Animal Image

        // Create Text Display
        GameObject textObj = new GameObject("InputText");
        textObj.transform.SetParent(canvas.transform, false);  // Added false parameter
        inputDisplay = textObj.AddComponent<TextMeshProUGUI>();
        RectTransform textRect = textObj.GetComponent<RectTransform>();
        textRect.anchorMin = new Vector2(0.5f, 1f);
        textRect.anchorMax = new Vector2(0.5f, 1f);
        textRect.pivot = new Vector2(0.5f, 1f);
        textRect.anchoredPosition = new Vector2(0, -420);
        textRect.sizeDelta = new Vector2(800, 100);
        inputDisplay.alignment = TextAlignmentOptions.Center;
        inputDisplay.fontSize = 72;
        inputDisplay.color = Color.black;
        inputDisplay.fontStyle = FontStyles.Bold;
        inputDisplay.characterSpacing = 15;
    }

    void CreateGround()
    {
        Debug.Log("Creating ground...");
        ground = new GameObject("Ground");

        if (ground != null)
        {
            ground.tag = "Ground";
            ground.transform.position = new Vector3(0, -4, 0);
            ground.transform.localScale = new Vector3(20, 2, 1); // Made ground thicker

            SpriteRenderer groundRenderer = ground.AddComponent<SpriteRenderer>();
            if (groundRenderer != null)
            {
                groundRenderer.color = new Color(0.6f, 0.4f, 0.2f); // Brown color
                // Create a solid white texture for the game
                Texture2D tex = new Texture2D(100, 100);
                Color[] colors = new Color[100 * 100];
                for (int i = 0; i < colors.Length; i++)
                    colors[i] = Color.white;
                tex.SetPixels(colors);
                tex.Apply();
                Sprite sprite = Sprite.Create(tex, new Rect(0, 0, 100, 100), new Vector2(0.5f, 0.5f));
                groundRenderer.sprite = sprite;
            }

            BoxCollider2D groundCollider = ground.AddComponent<BoxCollider2D>();
            groundCollider.size = new Vector2(1, 1); // Adjust collider to match visual size
        }
    }

    void CreatePlayer()
    {
        Debug.Log("Creating player...");
        bunnyPlayer = new GameObject("Player");
        bunnyPlayer.tag = "Player";
        bunnyPlayer.transform.position = new Vector3(-8, -3, 0);

        Sprite bunnySprite = Resources.Load<Sprite>("UIs/Bunny_animation/FREE/WhiteBunny_Walk/BunnyWalkLeftSide2-Sheet");
        if (bunnySprite == null)
        {
            Debug.LogError("Failed to load bunny sprite! Check path: UIs/Bunny_animation/FREE/WhiteBunny_Walk/BunnyWalkLeftSide2-Sheet");
            return;
        }

        SpriteRenderer renderer = bunnyPlayer.AddComponent<SpriteRenderer>();
        renderer.sprite = bunnySprite;
        renderer.sortingOrder = 1;

        // Increase bunny size
        bunnyPlayer.transform.localScale = new Vector3(3f, 3f, 1f);

        Rigidbody2D rb = bunnyPlayer.AddComponent<Rigidbody2D>();
        rb.freezeRotation = true;
        rb.constraints = RigidbodyConstraints2D.FreezeRotation;

        BoxCollider2D collider = bunnyPlayer.AddComponent<BoxCollider2D>();
        collider.size = new Vector2(0.3f, 0.3f);
        collider.offset = new Vector2(0, 0.15f);

        // Add PlayerController component
        bunnyPlayer.AddComponent<PlayerController>();
    }

    


    public void StartNewRound(bool keepCurrentAnimal = false)
    {
        Debug.Log("Starting new round...");
        if (availableAnimals == null || availableAnimals.Count == 0)
        {
            Debug.LogError("No animals available!");
            return;
        }

        if (!keepCurrentAnimal)
        {
            // Filter out used animals
            var availableNewAnimals = availableAnimals.Except(usedAnimals).ToList();

            if (availableNewAnimals.Count == 0)
            {
                // All animals have been used, reset the used animals list
                usedAnimals.Clear();
                availableNewAnimals = availableAnimals;
            }

            // Select a new random animal
            currentAnimal = availableNewAnimals[Random.Range(0, availableNewAnimals.Count)];
            usedAnimals.Add(currentAnimal);
        }

        Debug.Log($"Selected animal: {currentAnimal}");

        currentInput = "";
        wrongLetters.Clear();
        UpdateInputDisplay();

        // Load and display animal sprite
        Sprite animalSprite = Resources.Load<Sprite>($"UIs/animals/{currentAnimal}");
        if (animalSprite != null)
        {
            Debug.Log($"Loaded animal sprite: {currentAnimal}");
            animalImage.sprite = animalSprite;
            animalImage.preserveAspect = true;
        }
        else
        {
            Debug.LogError($"Failed to load animal sprite: {currentAnimal}");
        }

        CreateLetterObjects();

        // Resume game
        Time.timeScale = 1f;
    }
    public void RestartCurrentLevel()
    {
        StartNewRound(true);
        if (gameUI != null)
        {
            gameUI.HideRestartPanel();
        }
    }
    public void NextLevel()
    {
        Debug.Log("Starting next level with new animal");

        // Add current animal to used list if not already there
        if (!usedAnimals.Contains(currentAnimal))
        {
            usedAnimals.Add(currentAnimal);
        }

        // Get available animals that haven't been used
        List<string> remainingAnimals = availableAnimals.Except(usedAnimals).ToList();

        // If all animals have been used, reset the used list
        if (remainingAnimals.Count == 0)
        {
            usedAnimals.Clear();
            remainingAnimals = availableAnimals;
        }

        // Select new random animal
        currentAnimal = remainingAnimals[Random.Range(0, remainingAnimals.Count)];
        Debug.Log("Selected new animal: " + currentAnimal);

        // Reset game state
        currentInput = "";
        wrongLetters.Clear();

        // Reset bunny position
        if (bunnyPlayer != null)
        {
            bunnyPlayer.transform.position = new Vector3(-8, -3, 0);
        }

        // Load and display new animal sprite
        Sprite animalSprite = Resources.Load<Sprite>($"UIs/animals/{currentAnimal}");
        if (animalSprite != null)
        {
            animalImage.sprite = animalSprite;
            animalImage.preserveAspect = true;
        }

        // Update display
        UpdateInputDisplay();

        // Create new letters
        CreateLetterObjects();

        // Resume game
        Time.timeScale = 1f;
    }
    public void ContinueToNextLevel()
    {
        StartNewRound(false);
        if (gameUI != null)
        {
            gameUI.HideWinPanel();
        }
    }

    void CreateLetterObjects()
    {
        Debug.Log("Creating letter objects...");
        if (letterObjects != null)
        {
            foreach (GameObject letter in letterObjects)
            {
                if (letter != null) Destroy(letter);
            }
        }

        availableLetters = new List<char>();
        availableLetters.AddRange(currentAnimal.ToCharArray());

        // Ensure all letters are lowercase
        for (int i = 0; i < availableLetters.Count; i++)
        {
            availableLetters[i] = char.ToLower(availableLetters[i]);
        }

        // Add random letters until we reach letterCount
        while (availableLetters.Count < letterCount)
        {
            char randomLetter = (char)Random.Range('a', 'z' + 1);
            if (!availableLetters.Contains(randomLetter))
            {
                availableLetters.Add(randomLetter);
            }
        }

        // Randomize letter positions
        availableLetters = availableLetters.OrderBy(x => Random.value).ToList();

        letterObjects = new GameObject[availableLetters.Count];
        float spacing = 2f;
        float startX = -((availableLetters.Count - 1) * spacing) / 2;

        for (int i = 0; i < availableLetters.Count; i++)
        {
            GameObject letterObj = new GameObject($"Letter_{availableLetters[i]}");
            letterObj.transform.position = new Vector3(startX + (i * spacing), 2, 0);

            // Add necessary components
            SpriteRenderer renderer = letterObj.AddComponent<SpriteRenderer>();
            renderer.sortingOrder = 1;

            char letterToLoad = char.ToLower(availableLetters[i]);
            string letterPath = $"UIs/alphabetics_and_numbers/alphabetics_in_blue/{letterToLoad}";
            Sprite letterSprite = Resources.Load<Sprite>(letterPath);

            if (letterSprite == null)
            {
                Debug.LogError($"Failed to load sprite for letter: {letterToLoad}");
                continue;
            }

            renderer.sprite = letterSprite;
            renderer.transform.localScale = new Vector3(0.3f, 0.3f, 1f);

            // Add collider for triggering collection
            BoxCollider2D collider = letterObj.AddComponent<BoxCollider2D>();
            collider.isTrigger = true;
            collider.size = new Vector2(2f, 2f);

            // Add letter behavior component
            LetterBehavior behavior = letterObj.AddComponent<LetterBehavior>();
            behavior.letter = availableLetters[i];

            letterObjects[i] = letterObj;
        }
    }

    public void CollectLetter(char letter)
    {
        if (!currentAnimal.Contains(letter))
        {
            wrongLetters.Add(letter);
            if (wrongLetters.Count >= wrongLetterLimit)
            {
                if (gameUI != null)
                {
                    gameUI.ShowRestartPanel();
                }
            }
            return;
        }

        currentInput += letter;
        UpdateInputDisplay();

        if (IsWordComplete())
        {
            if (gameUI != null)
            {
                gameUI.ShowWinPanel();
            }
        }
    }


    void UpdateInputDisplay()
    {
        string displayText = "";
        foreach (char c in currentAnimal)
        {
            if (currentInput.Contains(c))
            {
                displayText += $"<color=green>{c}</color>";
            }
            else
            {
                displayText += "_";
            }
            displayText += " ";
        }

        if (wrongLetters.Count > 0)
        {
            displayText += "\n<color=red>Wrong: ";
            foreach (char c in wrongLetters)
            {
                displayText += c + " ";
            }
            displayText += "</color>";
        }

        inputDisplay.text = displayText;
    }

    bool IsWordComplete()
    {
        return currentAnimal.All(c => currentInput.Contains(c));
    }
    //Make sure that `LoadNewScene` does not exist in the `GameUI.cs`
    public void LoadNewScene()
    {
        UnityEngine.SceneManagement.SceneManager.LoadScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene().name);
    }
}


"""
################## Gane Manager agent

BLUE = "\033[94m"
RESET = "\033[0m"
UI_sugg = read_ui_suggestion()
class GameManagerAgent(DevelopmentAgent):
    def __init__(self):
        super().__init__("Game Manager Agent", BLUE)
    
    async def get_gemini_response(self):
        """Generate initial GameManager script"""
        
        
        prompt = fr"""You are a Game developer with the following tasks: 
        1- Create the Script for the game that would create GameObjects, Cameras, Canvas, Groundes, Players ... etc automatically. 
        2- The script should be based on the Brainstorming results and the UI existing assets. 
        3- You need to work only on the File [GameManager.cs] that initializes and manages a spelling game by setting up visual components, handling user input, and maintaining game state. It dynamically creates and resets elements like letters, the player character, and the environment while loading a set of available words for the game. Additionally, it ensures smooth gameplay by restarting rounds, updating UI elements, and managing interactions between objects
        4- Here is an example of the script to be inspired from: Edit, Modify, add functions or delete others based on the needs of the game: {Exemple} 
        5- Here is the UI assets: {UI_sugg}  
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
        6- Provide **structured output** with clear file boundaries:    - Use `### FILE START: [Full file path]` at the beginning of each file from C:\Users\user\My project (2)  (e.g., C:\Users\user\My project (2)\Assets\+file name ot folder + file name).    - Use `### FILE END` at the end of each file.
        
        
        IMPORTANT: The most important thing is that the goal is to create a whole game using only AND ONLY script the user should not interact with the GUI , create gameObjects ..etc , 100% Should be create only from script
        
        """
        
        return await self.generate_initial(prompt)
    
    async def handle_feedback(self, feedback, current_script):
        """Process feedback from the tester and update the script accordingly"""
        client = genai.Client(api_key=Gemini_key)
        chat = client.chats.create(model='gemini-2.0-flash-thinking-exp')
        
        prompt = f"""
    You are the Game Manager Agent responsible for Unity game setup.

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
        
        print(f"{self.color}Game Manager Agent processing feedback...{RESET}")
        response = await asyncio.to_thread(lambda: chat.send_message(prompt))
        response_text = response.text.strip()
        
        # Extract summary and script
        summary_match = re.search(r'<SUMMARY>(.*?)</SUMMARY>', response_text, re.DOTALL)
        script_match = re.search(r'<SCRIPT>(.*?)</SCRIPT>', response_text, re.DOTALL)
        
        summary = summary_match.group(1).strip() if summary_match else "No summary provided."
        updated_script = script_match.group(1).strip() if script_match else response_text
        
        # Print the summary
        print(f"{self.color}=== Game Manager Change Report ===")
        print(f"{self.color}{summary}{RESET}")
        print(f"{self.color}================================={RESET}")
        
        return updated_script