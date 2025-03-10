####### Game_Controller.py
import os
from google import genai
from conf import Gemini_key
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import re
import asyncio
from google import genai

Exemple=r"""using UnityEngine;

namespace AnimalSpellingGame
{
    public class PlayerController : MonoBehaviour
    {
        private Rigidbody2D rb;
        private bool isGrounded;
        private float moveSpeed = 5f;
        private float jumpForce = 10f;
        private SpriteRenderer spriteRenderer;

        // Camera bounds
        private float cameraLeftBound;
        private float cameraRightBound;

        void Start()
        {
            rb = GetComponent<Rigidbody2D>();
            spriteRenderer = GetComponent<SpriteRenderer>();

            // Calculate camera bounds
            Camera mainCamera = Camera.main;
            if (mainCamera != null)
            {
                float halfCameraWidth = mainCamera.orthographicSize * mainCamera.aspect;
                cameraLeftBound = mainCamera.transform.position.x - halfCameraWidth;
                cameraRightBound = mainCamera.transform.position.x + halfCameraWidth;
            }
            else
            {
                Debug.LogError("Main Camera not found! Player movement limits will not work.");
            }
        }

        void Update()
        {
            float moveInput = Input.GetAxis("Horizontal");
            rb.linearVelocity = new Vector2(moveInput * moveSpeed, rb.linearVelocity.y);

            // Flip sprite based on movement direction
            if (moveInput != 0)
            {
                spriteRenderer.flipX = moveInput < 0;
            }

            if (Input.GetKeyDown(KeyCode.Space) && isGrounded)
            {
                rb.AddForce(Vector2.up * jumpForce, ForceMode2D.Impulse);
            }

            // Keep player within camera bounds
            Vector3 clampedPosition = transform.position;
            clampedPosition.x = Mathf.Clamp(clampedPosition.x, cameraLeftBound + 1f, cameraRightBound - 1f); // Add padding
            transform.position = clampedPosition;
        }

        void OnCollisionEnter2D(Collision2D collision)
        {
            if (collision.gameObject.CompareTag("Ground"))
            {
                isGrounded = true;
            }
        }

        void OnCollisionExit2D(Collision2D collision)
        {
            if (collision.gameObject.CompareTag("Ground"))
            {
                isGrounded = false;
            }
        }
    }
}

----------------------------------------------------------------------------------------------------------------------------------------------------
using UnityEngine;

namespace AnimalSpellingGame
{
    public class LetterBehavior : MonoBehaviour
    {
        public char letter;
        private bool isCollected = false;

        private void OnTriggerEnter2D(Collider2D other)
        {
            if (!isCollected && other.CompareTag("Player"))
            {
                isCollected = true;
                FindObjectOfType<GameController>().CollectLetter(letter);
                gameObject.SetActive(false);  // Hide the letter after collection
            }
        }
        //You have to create a box colider for the letter and for the player as well
     
    }
}
----------------------------------------------------------------------------------------------------------------------------------------------------------
using UnityEngine;

public class GameLauncher : MonoBehaviour
{
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
    private static void InitializeGame()
    {
        // Create the MenuUI GameObject and attach the script
        GameObject menuObj = new GameObject("MenuUI");
        menuObj.AddComponent<MenuUI>();
    }
}

"""


##################################################### Game Controller Agent

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

YELLOW= "\033[93m"
RESET = "\033[0m"

class GameControllerAgent(DevelopmentAgent):

    def __init__(self):
        super().__init__("Game Controller Agent", YELLOW)
        
    async def get_gemini_response(self):
        """Generate initial scripts for PlayerController, LetterBehaviour, and GameLauncher"""
        UI_sugg = read_ui_suggestion()
        code=read_code('Game_Manager.md')
        prompt = fr"""
System Instruction:
You are a professional Unity game developer with expert knowledge in C# and Unity. Your task is to programmatically create complete game scenes using only code. Follow all instructions carefully and ensure your output adheres to the specified structure.

User Instructions:
1. Create C# scripts that programmatically generate all necessary game elements—including GameObjects, Cameras, Canvas, Grounds, Players, etc.—using only code.
2. Base your scripts on the provided brainstorming insights and the existing UI assets.
3. Work exclusively on these files:
   - PlayerController.cs
   - LetterBehaviour.cs
   - GameLauncher.cs
--PlayerController.cs
Description:
Handles player movement, jumping, and ensures the player stays within camera bounds.

Key Features:

Uses Rigidbody2D for physics-based movement.
Allows horizontal movement with the A and D keys (or arrow keys).
Supports jumping with the Space key when the player is grounded.
Flips the sprite based on movement direction.
Keeps the player within the camera's visible area.
Uses collision detection to check if the player is on the ground.
--LetterBehavior.cs
Description:
Manages collectible letters that the player interacts with.

Key Features:

Each letter has a unique character assigned to it.
Uses a trigger collider (OnTriggerEnter2D) to detect when the player collects a letter.
Calls the CollectLetter() function in GameController when collected.
Disables the letter object after collection.
Important: Requires both the letter and the player to have BoxCollider2D components.
--GameLauncher.cs
Description:
Initializes the game and ensures the MenuUI is available before the scene loads.

Key Features:

Runs before the scene loads using RuntimeInitializeOnLoadMethod.
Creates a MenuUI GameObject dynamically.
Attaches the MenuUI script to manage the game's main menu.
4. Use the example script provided for inspiration. Edit, modify, add, or remove functions as needed:
   {Exemple}
5. Incorporate the UI assets as provided:
   {UI_sugg}
6. Game manager script:
   {code}
7. Include brainstorming output for further context:
   {read_brainstorm_file()}

Structured Output Requirement:
- Your final output must clearly delineate each file.
- At the beginning of each file, insert a line in the following format:
    ### FILE START: [Full file path]
  (e.g., "### FILE START: C:\Users\user\My project (2)\Assets\Scripts\PlayerController.cs")
- At the end of each file, add the line:
    ### FILE END

Coding Guidelines:
1. Import all necessary Unity namespaces (e.g., using UnityEngine; using System.Collections;).
2. Every MonoBehaviour class must include appropriate lifecycle methods (e.g., Awake, Start, Update) as needed.
3. Always initialize variables before using them.
4. Check for null references before accessing any properties or methods.
5. Ensure proper bracing and method structure, balancing all opening and closing braces.
6. When referencing other scripts, use GetComponent safely.
7. Implement inheritance and interfaces correctly.
8. Use forward declarations for any scripts that are referenced but not yet defined.
IMPORTANT: The most important thing is that the goal is to create a whole game using only AND ONLY script the user should not interact with the GUI , create gameObjects ..etc , 100% Should be create only from script
"""
        
        return await self.generate_initial(prompt)
    
    async def handle_feedback(self, feedback, current_script):
        """Process feedback from the tester and update the script accordingly"""
        client = genai.Client(api_key=Gemini_key)
        chat = client.chats.create(model='gemini-2.0-flash-thinking-exp')
        
        prompt = f"""
    You are the Game Controller Agent responsible for Unity game setup.

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
IMPORTANT: The most important thing is that the goal is to create a whole game using only AND ONLY script the user should not interact with the GUI , create gameObjects ..etc , 100% Should be create only from script

    """
        
        print(f"{self.color}Game Controller Agent processing feedback...{RESET}")
        response = await asyncio.to_thread(lambda: chat.send_message(prompt))
        response_text = response.text.strip()
        
        # Extract summary and script
        summary_match = re.search(r'<SUMMARY>(.*?)</SUMMARY>', response_text, re.DOTALL)
        script_match = re.search(r'<SCRIPT>(.*?)</SCRIPT>', response_text, re.DOTALL)
        
        summary = summary_match.group(1).strip() if summary_match else "No summary provided."
        updated_script = script_match.group(1).strip() if script_match else response_text
        
        # Print the summary
        print(f"{self.color}=== Game Controller Change Report ===")
        print(f"{self.color}{summary}{RESET}")
        print(f"{self.color}================================={RESET}")
        
        return updated_script
    

