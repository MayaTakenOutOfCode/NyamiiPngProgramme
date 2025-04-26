import pygame
import sounddevice as sd
import numpy as np
import math
import threading
import time
import random
import queue
import json
from vosk import Model, KaldiRecognizer

# CONSTANTS
WINDOW_HEIGHT = 800
WINDOW_WIDTH = 800
THRESHOLD = 0.2
BOUNCE_SPEED = 5
BOUNCE_HEIGHT = 10

BREATH_SPEED = 1
BREATH_HEIGHT = 5

IMAGE_SCALE = 0.4  # Adjust image size

# INIT pygame
pygame.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Nyamii OBS GreenScreen")

idle_img = pygame.image.load("nyamii/idle.png")
talking_img = pygame.image.load("nyamii/talking.png")
heart_img = pygame.image.load("assets/heart.png")
sparkle_img = pygame.image.load("assets/sparkle.png")  # <-- you'll need a sparkle image too!!

# Scale images
idle_img = pygame.transform.scale(idle_img, (int(idle_img.get_width() * IMAGE_SCALE), int(idle_img.get_height() * IMAGE_SCALE)))
talking_img = pygame.transform.scale(talking_img, (int(talking_img.get_width() * IMAGE_SCALE), int(talking_img.get_height() * IMAGE_SCALE)))
heart_img = pygame.transform.scale(heart_img, (int(heart_img.get_width() * 0.2), int(heart_img.get_height() * 0.2)))
sparkle_img = pygame.transform.scale(sparkle_img, (32, 32))  # cute sparkle size!

current_img = idle_img
is_talking = False
particles = []  # hearts + sparkles together now

# For pink glow effect
glow_timer = 0
GLOW_DURATION = 180  # glow stays longer now because more hearts! 💖

# Global audio queue for vosk
q = queue.Queue()

# Mic volume + audio capture
def audio_callback(indata, frames, time_info, status):
    global is_talking
    volume_norm = np.linalg.norm(indata) * 10
    is_talking = volume_norm > THRESHOLD
    q.put(bytes(indata))  # Send to Vosk queue too

def start_mic_detection():
    with sd.InputStream(samplerate=16000, dtype='int16', channels=1, callback=audio_callback):
        while True:
            time.sleep(0.1)

# Create hearts and sparkles
def trigger_magic():
    global glow_timer
    glow_timer = GLOW_DURATION
    for _ in range(100):
        particles.append({
            "type": "heart",
            "img": heart_img,
            "x": random.randint(0, WINDOW_WIDTH),
            "y": random.randint(-400, 0),
            "speed_x": random.uniform(-1.5, 1.5),
            "speed_y": random.uniform(1, 3),
            "timer": random.randint(120, 200),
            "scale": random.uniform(0.8, 1.2)
        })
    for _ in range(50):  # extra 50 sparkles!!
        particles.append({
            "type": "sparkle",
            "img": sparkle_img,
            "x": random.randint(0, WINDOW_WIDTH),
            "y": random.randint(-400, 0),
            "speed_x": random.uniform(-1, 1),
            "speed_y": random.uniform(0.5, 2),
            "timer": random.randint(100, 180),
            "scale": random.uniform(0.5, 1.5)
        })

# Keyword listener
def listen_for_keywords():
    model = Model("vosk-model-small-en-us-0.15")
    recognizer = KaldiRecognizer(model, 16000)
    keywords = ["love", "heart", "cute", "hug", "adorable"]

    while True:
        data = q.get()
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower()
            if text:
                print("Heard:", text)
                if any(word in text for word in keywords):
                    trigger_magic()

# Threads
mic_thread = threading.Thread(target=start_mic_detection)
mic_thread.daemon = True
mic_thread.start()

keyword_thread = threading.Thread(target=listen_for_keywords)
keyword_thread.daemon = True
keyword_thread.start()

# Game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # GREEN SCREEN BACKGROUND!!!
    window.fill((0, 255, 0))

    elapsed_time = time.time() - start_time

    # Bounce breathing / talking
    if is_talking:
        current_img = talking_img
        bounce_offset = math.sin(elapsed_time * BOUNCE_SPEED) * BOUNCE_HEIGHT
    else:
        current_img = idle_img
        bounce_offset = math.sin(elapsed_time * BREATH_SPEED) * BREATH_HEIGHT

    # Draw character with glow if active
    char_x = WINDOW_WIDTH // 2 - current_img.get_width() // 2
    char_y = WINDOW_HEIGHT // 2 - current_img.get_height() // 2 + bounce_offset

    if glow_timer > 0:
        glow_surface = pygame.Surface((current_img.get_width() + 80, current_img.get_height() + 80), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surface, (255, 182, 193, 150), glow_surface.get_rect())  # Pink glow
        window.blit(glow_surface, (char_x - 40, char_y - 40))
        glow_timer -= 1

    window.blit(current_img, (char_x, char_y))

    # Update and draw particles
    for particle in particles[:]:
        particle["x"] += particle["speed_x"]
        particle["y"] += particle["speed_y"]
        particle["timer"] -= 1
        scaled_img = pygame.transform.scale(particle["img"], (int(particle["img"].get_width() * particle["scale"]), int(particle["img"].get_height() * particle["scale"])))
        window.blit(scaled_img, (particle["x"], particle["y"]))
        if particle["timer"] <= 0 or particle["y"] > WINDOW_HEIGHT:
            particles.remove(particle)

    pygame.display.update()
    clock.tick(60)

pygame.quit()
sd.stop()
