# yt_connect.py

import pytchat
import time
import threading

# Constant keyword dictionary
KEYWORDS = {
    "bald": "makes model bald",
    "neko": "makes model a neko",
    "evil": "succubus neko model",
    "human": "human model",
    "eyes": "gives model googly eyes",
    "bonk": "makes model a bonk",
    "cheese": "throws cheese at tuber",
    "cool": "gives model a cool sunglasses"
}

# Where detected events will be stored
event_queue = []

def _watch_live_chat(video_id):
    chat = pytchat.create(video_id=video_id)
    print(f"Watching live chat for video ID: {video_id}")

    while chat.is_alive():
        try:
            for c in chat.get().sync_items():
                message = c.message.lower()
                for keyword, action in KEYWORDS.items():
                    if keyword in message:
                        event_queue.append((c.author.name, keyword, action))
            time.sleep(1)  
        except Exception as e:
            print(f"Chat watcher error: {e}")
            time.sleep(5)  

def start_chat_listener(video_id):
    """
    Starts the chat listener in a separate thread.
    """
    thread = threading.Thread(target=_watch_live_chat, args=(video_id,), daemon=True)
    thread.start()

def check_keywords():
    """
    Returns all chat events (and clears them).
    Each event is (author, keyword, action).
    """
    events = event_queue.copy()
    event_queue.clear()
    return events
