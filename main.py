import pygame
import sounddevice as sd
import numpy as np
import math
import threading
import time
import random
import queue
from yt_connect import start_chat_listener, check_keywords 
import json
from vosk import Model, KaldiRecognizer
import sys
import os 

# --- MODEL CHANGER PATHS ---

pathToModelDir = os.path.join(os.path.dirname(__file__), "nyamii/models")
pathTobaldModel = os.path.join(pathToModelDir, "bald")
pathToBonkModel = os.path.join(pathToModelDir, "bonk")
pathToCoolModel = os.path.join(pathToModelDir, "cool")
pathToEvilModel = os.path.join(pathToModelDir, "evil")
pathToGooglyModel = os.path.join(pathToModelDir, "googly")
pathToHumanModel = os.path.join(pathToModelDir, "human")
pathToNekoModel = os.path.join(pathToModelDir, "neko")
pathToNyamiiModel = os.path.join(pathToModelDir, "nyamii")

#Functions for keywords
def make_neko():
    change_model("neko")
    print("Making model a Neko!")
def make_bald():
    change_model("bald")
    print("Making model into bald model!")
def make_evil():
    change_model("evil")
    print("Making model a succubus!")
def make_googly():
    change_model("googly")
    print("Giving model googly eyes!")
def make_bonk():
    print("Making model a bonk!")
def throw_cheese():
    print("Throwing cheese at the tuber!")
def make_cool():
    print("Giving model cool sunglasses!")
def make_human():
    change_model("human")
    print("Making model human!")
# start_chat_listener("YOUR_VIDEO_ID") 
# check_keywords()
# if check_keywords().event_queue != []:
#     for event in check_keywords().event_queue:
#         author, keyword, action = event
#         print(f"Keyword '{keyword}' detected from {author}: {action}")
#         if keyword == "bald":
#             make_bald()
#         elif keyword == "neko":
#             make_neko()
#         elif keyword == "evil":
#             make_evil()
#         elif keyword == "googly":
#             make_googly()
#         # elif keyword == "bonk":
#         #     make_bonk()
#         # elif keyword == "cheese":
#         #     throw_cheese()
#         # elif keyword == "cool":
#         #     make_cool()
#         elif keyword == "human":
#             make_human()
# --- CONSTANTS ---
WINDOW_HEIGHT = 800
WINDOW_WIDTH = 800
THRESHOLD = 12 # Mic volume threshold for talking state
BOUNCE_SPEED = 5
BOUNCE_HEIGHT = 10
BREATH_SPEED = 1
BREATH_HEIGHT = 5
IMAGE_SCALE = 0.8
SPLASH_DURATION = 2000 # Milliseconds (2 seconds)



# Game States
SPLASH = 0
MENU = 1
GAME = 2

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN_SCREEN = (0, 255, 0) # Default background for game
GREY = (50, 50, 50)
LIGHT_GREY = (100, 100, 100)
PINK = (255, 182, 193)
HIGHLIGHT_COLOR = PINK # Color for button hover
POPUP_BG_COLOR = (40, 40, 60)
POPUP_BORDER_COLOR = (150, 150, 180)
OVERLAY_COLOR = (0, 0, 0, 180) # Semi-transparent black for overlay

# Popup Menu Constants
POPUP_WIDTH = 400
POPUP_HEIGHT = 450
POPUP_X = (WINDOW_WIDTH - POPUP_WIDTH) // 2
POPUP_Y = (WINDOW_HEIGHT - POPUP_HEIGHT) // 2
POPUP_BORDER_WIDTH = 2

# --- PYGAME INIT ---
pygame.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Nyamii OBS GreenScreen")
clock = pygame.time.Clock()
app_start_time = pygame.time.get_ticks() # For splash screen timing
game_start_time = 0 # Reset when game actually starts

# --- FONT LOADING ---
try:
    font_default_L = pygame.font.SysFont(None, 72)
    font_default_M = pygame.font.SysFont(None, 50)
    font_default_S = pygame.font.SysFont(None, 40) 
    font_default_XS = pygame.font.SysFont(None, 30) 
except Exception as e:
    print(f"Error loading system font: {e}. Using Pygame default.")
    font_default_L = pygame.font.Font(None, 72)
    font_default_M = pygame.font.Font(None, 50)
    font_default_S = pygame.font.Font(None, 40)
    font_default_XS = pygame.font.Font(None, 30)

# --- Model loading function ---

def load_model(model_name):
    global current_model_images, current_model_name, heart_img, sparkle_img, cheese_img

    # Define paths for model and assets
    model_folder = os.path.join(pathToModelDir, model_name)
    assets_folder = os.path.join(base_path, "assets")

    try:
        # Load the model images (idle and talking)
        idle_path = os.path.join(model_folder, f"{model_name}.png")
        talking_path = os.path.join(model_folder, f"{model_name}Talking.png")

        current_idle_img = pygame.image.load(idle_path).convert_alpha()
        current_talking_img = pygame.image.load(talking_path).convert_alpha()

        # Apply scaling to the model images
        current_idle_img = pygame.transform.scale(
            current_idle_img, 
            (int(current_idle_img.get_width() * IMAGE_SCALE), int(current_idle_img.get_height() * IMAGE_SCALE))
        )
        current_talking_img = pygame.transform.scale(
            current_talking_img, 
            (int(current_talking_img.get_width() * IMAGE_SCALE), int(current_talking_img.get_height() * IMAGE_SCALE))
        )

        # Update the global dictionary with the loaded and scaled images
        current_model_images = {'idle': current_idle_img, 'talking': current_talking_img}

        # Set the current model name
        current_model_name = model_name
        print(f"Loaded model: {model_name}")

        # Load and scale the other assets
        heart_img = pygame.image.load(os.path.join(assets_folder, "heart.png")).convert_alpha()
        heart_img = pygame.transform.scale(heart_img, (int(heart_img.get_width() * 0.2), int(heart_img.get_height() * 0.2)))

        sparkle_img = pygame.image.load(os.path.join(assets_folder, "sparkle.png")).convert_alpha()
        sparkle_img = pygame.transform.scale(sparkle_img, (32, 32))

        #cheese_img = pygame.image.load(os.path.join(assets_folder, "cheese.png")).convert_alpha()

    except pygame.error as e:
        print(f"Error loading model images: {e}")
        print(f"Please ensure image files exist in '{model_folder}/' and '{assets_folder}/'.")
        pygame.quit()
        sys.exit()



# --- LOAD ASSETS ---
# Define base path (useful if assets are in subdirs)
base_path = os.path.dirname(__file__) # Directory where the script is running
nyamii_path = os.path.join(base_path, "nyamii")
assets_path = os.path.join(base_path, "assets")

# try:
#     idle_img = pygame.image.load(os.path.join(nyamii_path, "idle.png")).convert_alpha()
#     talking_img = pygame.image.load(os.path.join(nyamii_path, "talking.png")).convert_alpha()
#     heart_img = pygame.image.load(os.path.join(assets_path, "heart.png")).convert_alpha()
#     sparkle_img = pygame.image.load(os.path.join(assets_path, "sparkle.png")).convert_alpha()
#     cheese_img = pygame.image.load(os.path.join(assets_path, "cheese.png")).convert_alpha()
# except pygame.error as e:
#     print(f"Error loading image: {e}")
#     print(f"Please ensure image files exist in '{nyamii_path}/' and '{assets_path}/'.")
#     pygame.quit()
#     sys.exit()

load_model("nyamii")
# # --- SCALE ASSETS ---
# idle_img = pygame.transform.scale(idle_img, (int(idle_img.get_width() * IMAGE_SCALE), int(idle_img.get_height() * IMAGE_SCALE)))
# talking_img = pygame.transform.scale(talking_img, (int(talking_img.get_width() * IMAGE_SCALE), int(talking_img.get_height() * IMAGE_SCALE)))
# heart_img = pygame.transform.scale(heart_img, (int(heart_img.get_width() * 0.2), int(heart_img.get_height() * 0.2)))
# sparkle_img = pygame.transform.scale(sparkle_img, (32, 32))

# --- update model images ---
def update_current_model_images():
    global current_model_images
    current_model_images = {
        'idle': current_idle_img,
        'talking': current_talking_img
    }



# --- GAME VARIABLES ---
current_model_images = {'idle': None, 'talking': None}  # Set initial values to None
current_img = None  # Set initial value to None
is_talking = False
particles = []
glow_timer = 0
GLOW_DURATION = 180
global is_options_popup_open # Flag for the options popup
is_options_popup_open = False
# You would call load_model here to set the initial model and images
def initialize_model(model_name):
    load_model(model_name)  # This will load the model and update current_model_images
    global current_img
    current_img = current_model_images['idle']  # Set the initial image to the idle state

initialize_model('nyamii')


# Global audio queue shared between mic input and keyword listener
q = queue.Queue()

vosk_model = None
try:
    # Attempt to pre-load model to avoid delay when starting game
    model_path = os.path.join(base_path, "vosk-model-small-en-us-0.15") # Assuming model is in script dir
    if os.path.exists(model_path):
        vosk_model = Model(model_path)
        print("Vosk model loaded.")
    else:
        print(f"Vosk model not found at '{model_path}'. Keyword listener disabled.")
except Exception as e:
    print(f"Error loading Vosk model: {e}")
    vosk_model = None # Ensure it's None if loading fails


# --- AUDIO & KEYWORD FUNCTIONS ---
def audio_callback(indata, frames, time_info, status):
    """Called by sounddevice for each audio chunk; updates talking state and queues data for Vosk."""
    global is_talking
    volume_norm = np.sqrt(np.mean(indata**2)) # RMS volume calculation
    is_talking = volume_norm > THRESHOLD
    if vosk_model:
        q.put(bytes(indata))

def start_mic_detection():
    """Starts the sounddevice input stream in a separate thread."""
    try:
        # Context manager ensures the stream is closed automatically
        with sd.InputStream(samplerate=16000, dtype='int16', channels=1, callback=audio_callback):
            print("Microphone stream started.")
            # Keep thread alive while main program runs (or until an error)
            while threading.current_thread().is_alive():
                time.sleep(0.1)
    except Exception as e:
        print(f"Error starting audio stream: {e}. Check mic settings/permissions.")

def trigger_magic():
    """Creates particle effects (hearts, sparkles) and activates glow."""
    global glow_timer
    glow_timer = GLOW_DURATION
    center_x = WINDOW_WIDTH // 2
    center_y = WINDOW_HEIGHT // 2
    spawn_radius = 150 # Spawn closer to character

    # Create hearts near center
    for _ in range(60): # Reduced amount for potentially better performance
        angle = random.uniform(0, 2 * math.pi)
        offset_x = random.uniform(0, spawn_radius)
        offset_y = random.uniform(-spawn_radius, spawn_radius) # Spawn slightly above too
        particles.append({
            "type": "heart", "img": heart_img,
            "x": center_x + offset_x * math.cos(angle), "y": center_y + offset_y,
            "speed_x": random.uniform(-1.0, 1.0), "speed_y": random.uniform(0.5, 2.5),
            "timer": random.randint(100, 180), "scale": random.uniform(0.7, 1.1)
        })
    # Create sparkles near center
    for _ in range(30): # Reduced amount
        angle = random.uniform(0, 2 * math.pi)
        offset_x = random.uniform(0, spawn_radius)
        offset_y = random.uniform(-spawn_radius, spawn_radius)
        particles.append({
            "type": "sparkle", "img": sparkle_img,
             "x": center_x + offset_x * math.cos(angle), "y": center_y + offset_y,
            "speed_x": random.uniform(-0.8, 0.8), "speed_y": random.uniform(0.3, 1.8),
            "timer": random.randint(80, 160), "scale": random.uniform(0.5, 1.3)
        })

def listen_for_keywords():
    """Runs in a thread, processes audio queue with Vosk, triggers effects on keywords."""
    if not vosk_model: return # Exit if model didn't load

    recognizer = KaldiRecognizer(vosk_model, 16000)
    keywords = ["love", "heart", "cute", "hug", "adorable", "thank you", "thanks",
                "awesome", "amazing", "wow", "cool", "nice", "boss girl"]
    print(f"Keyword listener started. Keywords: {keywords}")

    while threading.current_thread().is_alive():
        try:
            data = q.get(timeout=1)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()
                if text:
                    print("Heard:", text)
                    # Use a generator expression for slightly cleaner check
                    if any(word in text for word in keywords):
                        print("Keyword detected! Triggering magic...")
                        trigger_magic()
        except queue.Empty:
            continue # Loop normally if no audio data after timeout
        except Exception as e:
            print(f"Error in keyword listener: {e}")
            time.sleep(1) # Prevent spamming logs on repeated errors

    print("Keyword listener stopped.")

# --- THREADS (Define placeholders; start when game begins) ---
mic_thread = None
keyword_thread = None

# --- DRAW FUNCTIONS ---

def draw_splash_screen():
    """Draws the initial loading splash screen."""
    window.fill(GREY)
    splash_text = font_default_L.render("Nyamii Loading...", True, WHITE)
    text_rect = splash_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
    window.blit(splash_text, text_rect)

def draw_main_menu(buttons, mouse_pos):
    """Draws the main menu screen with title and buttons."""
    window.fill(GREY)
    title_text = font_default_L.render("Nyamii VTuber", True, WHITE) # Simplified title
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
    window.blit(title_text, title_rect)

    for name, rect in buttons.items():
        color = HIGHLIGHT_COLOR if rect.collidepoint(mouse_pos) else WHITE
        button_text = font_default_M.render(name, True, color)
        text_rect = button_text.get_rect(center=rect.center)
        window.blit(button_text, text_rect)

def draw_game_screen(elapsed_time):
    """Draws the main game elements: background, character, particles, glow."""
    global current_img, glow_timer # Declare modification intent

    window.fill(GREEN_SCREEN) # Default green screen

    # Character bounce based on talking state
    if is_talking:
        current_img = current_model_images['talking']  # Use loaded 'talking' image
        bounce_offset = math.sin(elapsed_time * BOUNCE_SPEED) * BOUNCE_HEIGHT
    else:
        current_img = current_model_images['idle']  # Use loaded 'idle' image
        bounce_offset = math.sin(elapsed_time * BREATH_SPEED) * BREATH_HEIGHT

    char_x = WINDOW_WIDTH // 2 - current_img.get_width() // 2
    char_y = WINDOW_HEIGHT // 2 - current_img.get_height() // 2 + int(bounce_offset)  # Ensure int

    # Draw pink glow effect if active
    if glow_timer > 0:
        glow_radius_x = current_img.get_width() // 2 + 40
        glow_radius_y = current_img.get_height() // 2 + 40
        glow_center = (char_x + current_img.get_width() // 2, char_y + current_img.get_height() // 2)

        glow_surface_size = (glow_radius_x * 2, glow_radius_y * 2)
        glow_surface = pygame.Surface(glow_surface_size, pygame.SRCALPHA)

        # Calculate alpha for fade-out effect
        max_alpha = 150
        current_alpha = int(max_alpha * (glow_timer / GLOW_DURATION))
        glow_color = (PINK[0], PINK[1], PINK[2], max(0, min(current_alpha, 255)))  # Clamp alpha

        pygame.draw.ellipse(glow_surface, glow_color, glow_surface.get_rect())

        glow_blit_pos = (glow_center[0] - glow_radius_x, glow_center[1] - glow_radius_y)
        window.blit(glow_surface, glow_blit_pos)
        glow_timer -= 1

    # Draw the character image
    window.blit(current_img, (char_x, char_y))

    # Update and draw particles (iterate over a copy for safe removal)
    for particle in particles[:]:
        particle["x"] += particle["speed_x"]
        particle["y"] += particle["speed_y"]
        particle["timer"] -= 1

        # Simple scaling and drawing
        scaled_img = pygame.transform.scale(particle["img"], (int(particle["img"].get_width() * particle["scale"]), int(particle["img"].get_height() * particle["scale"])))
        window.blit(scaled_img, (int(particle["x"]), int(particle["y"])))  # Ensure int coords

        # Remove particle if timer runs out or it goes off-screen (bottom)
        if particle["timer"] <= 0 or particle["y"] > WINDOW_HEIGHT:
            particles.remove(particle)

def draw_options_popup(buttons, mouse_pos):
    """Draws the semi-transparent overlay and the options popup menu."""
    # Draw semi-transparent overlay
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill(OVERLAY_COLOR)
    window.blit(overlay, (0, 0))

    # Draw popup background and border
    popup_rect = pygame.Rect(POPUP_X, POPUP_Y, POPUP_WIDTH, POPUP_HEIGHT)
    pygame.draw.rect(window, POPUP_BG_COLOR, popup_rect, border_radius=10)
    pygame.draw.rect(window, POPUP_BORDER_COLOR, popup_rect, POPUP_BORDER_WIDTH, border_radius=10)

    # Draw popup title
    title_text = font_default_XS.render("Options (Press ESC to Close)", True, WHITE)
    title_rect = title_text.get_rect(center=(popup_rect.centerx, popup_rect.top + 30))
    window.blit(title_text, title_rect)

    # Draw buttons
    for name, rect in buttons.items():
        color = HIGHLIGHT_COLOR if rect.collidepoint(mouse_pos) else WHITE
        button_text = font_default_S.render(name, True, color)
        text_rect = button_text.get_rect(center=rect.center)
        window.blit(button_text, text_rect)


# --- Button Definitions ---
menu_buttons = {
    "Start": pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 + 0, 300, 50),
    "Quit": pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 + 70, 300, 50)
}

# Define popup buttons relative to popup window
popup_button_width = POPUP_WIDTH - 80
popup_button_height = 50
popup_start_y = POPUP_Y + 80
popup_button_x = POPUP_X + (POPUP_WIDTH - popup_button_width) // 2
popup_button_spacing = 65

popup_buttons = {
    "Switch Model": pygame.Rect(popup_button_x, popup_start_y, popup_button_width, popup_button_height),
    "Add Prop": pygame.Rect(popup_button_x, popup_start_y + popup_button_spacing, popup_button_width, popup_button_height),
    "Add Background": pygame.Rect(popup_button_x, popup_start_y + 2 * popup_button_spacing, popup_button_width, popup_button_height),
    "Change Scene": pygame.Rect(popup_button_x, popup_start_y + 3 * popup_button_spacing, popup_button_width, popup_button_height),

    "Close Menu": pygame.Rect(popup_button_x, POPUP_Y + POPUP_HEIGHT - popup_button_height - 30, popup_button_width, popup_button_height) # Position Close at bottom
}

import pygame
import sys

def change_model():
    global current_img, current_model_images, current_model_name, is_options_popup_open

    font = pygame.font.Font(None, 36)  # Use a basic font
    input_box = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 20, 300, 40)  # Define the input box
    color_inactive = pygame.Color('lightskyblue3')  # Inactive color
    color_active = pygame.Color('dodgerblue2')  # Active color
    color = color_inactive
    active = False
    text = ''  # Initial text in the input box
    clock = pygame.time.Clock()
    running_input = True

    while running_input:
        window.fill(GREEN_SCREEN)  # Clear the window
        
        # Event handling for input box
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Toggle active status of the input box when clicked
                if input_box.collidepoint(event.pos):
                    active = True
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        # When Enter is pressed, attempt to load the model
                        if text:  # Check if there's text in the box
                            load_model(text)  # Load the model based on the text input
                            print(f"Model changed to: {text}")
                            is_options_popup_open = False  # Close options popup
                            running_input = False  # Exit the input loop
                            return  # Return to main game loop
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]  # Handle backspace to delete characters
                    elif event.key == pygame.K_ESCAPE:
                        # Allow ESC to cancel input and return to game
                        running_input = False
                        return
                    else:
                        text += event.unicode  # Add typed character to text

        # Render prompt text
        prompt_text = font.render("Enter model name:", True, WHITE)
        window.blit(prompt_text, (WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 60))

        # Render the text and input box
        txt_surface = font.render(text, True, color)
        width = max(300, txt_surface.get_width() + 10)
        input_box.w = width
        window.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(window, color, input_box, 2)  # Draw the input box border
        
        # Update the display
        pygame.display.flip()
        clock.tick(30)  # Set frame rate to 30 fps
# --- MAIN LOOP ---
running = True
game_state = SPLASH

while running:
    mouse_pos = pygame.mouse.get_pos()
    events = pygame.event.get() # Get events once per frame

    # --- Global Event Handling (Applies to all states) ---
    for event in events:
        if event.type == pygame.QUIT:
            running = False

    # --- State-Specific Logic & Event Handling ---
    if game_state == SPLASH:
        draw_splash_screen()
        if pygame.time.get_ticks() - app_start_time > SPLASH_DURATION:
            game_state = MENU

    elif game_state == MENU:
        for event in events: # Process events specific to MENU
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu_buttons["Start"].collidepoint(mouse_pos):
                    print("Starting game...")
                    game_state = GAME
                    game_start_time = time.time() # Reset game timer for animations
                    is_options_popup_open = False # Ensure popup is closed on game start

                    # --- START BACKGROUND THREADS ---
                    if mic_thread is None or not mic_thread.is_alive():
                         mic_thread = threading.Thread(target=start_mic_detection, daemon=True)
                         mic_thread.start()
                    if vosk_model and (keyword_thread is None or not keyword_thread.is_alive()):
                         keyword_thread = threading.Thread(target=listen_for_keywords, daemon=True)
                         keyword_thread.start()
                    elif not vosk_model:
                        print("Keyword listener disabled - Vosk model not loaded.")

                elif menu_buttons["Quit"].collidepoint(mouse_pos):
                    running = False
        # Drawing for MENU state
        draw_main_menu(menu_buttons, mouse_pos)


    elif game_state == GAME:
        # --- GAME Event Handling ---
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    is_options_popup_open = not is_options_popup_open # Toggle popup
                    print(f"Options Popup: {'Open' if is_options_popup_open else 'Closed'}")

            if is_options_popup_open:
                 if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked_on_button = False
                    # Check clicks on popup buttons
                    for name, rect in popup_buttons.items():
                        if rect.collidepoint(mouse_pos):
                            print(f"Popup Option Clicked: {name}")
                            # --- Placeholder Actions ---
                            if name == "Close Menu":
                                is_options_popup_open = False
                            elif name == "Switch Model":
                                change_model()
                                is_options_popup_open = False # Close after action (optional)
                            elif name == "Add Prop":
                                print("Action: Implement prop adding logic")
                                is_options_popup_open = False
                            elif name == "Add Background":
                                print("Action: Implement background adding logic")
                                is_options_popup_open = False
                            elif name == "Change Scene":
                                print("Action: Implement scene changing logic")
                                is_options_popup_open = False
                            clicked_on_button = True
                            break # Exit loop once a button is clicked

                    # If click was not on a button, check if it was outside the popup rect
                    if not clicked_on_button:
                         popup_rect = pygame.Rect(POPUP_X, POPUP_Y, POPUP_WIDTH, POPUP_HEIGHT)
                         if not popup_rect.collidepoint(mouse_pos):
                             is_options_popup_open = False # Close if clicked outside
                             print("Clicked outside popup, closing.")

            


        # --- GAME Drawing Logic ---
        elapsed_time = time.time() - game_start_time
        draw_game_screen(elapsed_time)

        # Draw popup on top if it's open
        if is_options_popup_open:
            draw_options_popup(popup_buttons, mouse_pos)


    # --- Update Display ---
    pygame.display.update()
    clock.tick(60) # Cap FPS at 60

# --- Cleanup ---
print("Exiting application...")
pygame.quit()
print("Pygame quit.")
sys.exit()