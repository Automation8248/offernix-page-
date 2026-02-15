import os
import json
import random
import requests
import re
import datetime
import urllib.parse

# --- CONFIGURATION ---
VIDEO_FOLDER = "videos"
HISTORY_FILE = "history.json"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY")  # Format: username/repo
BRANCH_NAME = "main"  # Ya 'master' check kar lena

# --- HELPER FUNCTIONS ---

def clean_text(text):
    """
    User condition: No *, ., #, or brackets [] ()
    """
    # Remove specific characters
    cleaned = re.sub(r'[*\.#\[\]\(\)]', '', text)
    # Remove multiple spaces and strip
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def get_pollination_text(filename):
    """
    Uses Pollination AI (No API Key) to generate text based on filename.
    """
    clean_filename = filename.replace("_", " ").replace("-", " ").split(".")[0]
    
    # Prompt engineering specifically for this logic
    prompt = (
        f"Write a short engaging viral caption for a video titled '{clean_filename}'. "
        "Include SEO keywords at the end. "
        "Do not use emojis. Keep it under 50 words."
    )
    
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://text.pollinations.ai/{encoded_prompt}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            raw_text = response.text
            
            # Text ko clean karte hain (No dots, stars, hashes)
            final_text = clean_text(raw_text)
            
            # Title generate karte hain (First 5 words of caption)
            title = " ".join(final_text.split()[:6])
            
            return title, final_text
        else:
            return clean_filename, f"Watch this amazing video about {clean_filename}"
    except Exception as e:
        print(f"AI Generation Failed: {e}")
        return clean_filename, f"Watch this amazing video about {clean_filename}"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, 'r') as f:
        return json.load(f)

def save_history(data):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- MAIN LOGIC ---

def run_automation():
    # 1. Purani files delete karo (15 days rule)
    history = load_history()
    today = datetime.date.today()
    new_history = []
    
    print("Checking for files to delete (older than 15 days)...")
    for entry in history:
        sent_date = datetime.date.fromisoformat(entry['date_sent'])
        days_diff = (today - sent_date).days
        
        file_path = os.path.join(VIDEO_FOLDER, entry['filename'])
        
        if days_diff >= 15:
            # Delete file physically
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"DELETED EXPIRED VIDEO: {entry['filename']}")
            else:
                print(f"File already gone: {entry['filename']}")
            # History se remove (by not adding to new_history)
        else:
            new_history.append(entry)
    
    # Save clean history immediately
    save_history(new_history)
    history = new_history # Update local variable

    # 2. Pick New Video
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)
        
    all_videos = [f for f in os.listdir(VIDEO_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.mkv'))]
    sent_filenames = [entry['filename'] for entry in history]
    
    available_videos = [v for v in all_videos if v not in sent_filenames]
    
    if not available_videos:
        print("No new videos to send.")
        return

    video_to_send = random.choice(available_videos)
    video_path = os.path.join(VIDEO_FOLDER, video_to_send)
    
    print(f"Selected Video: {video_to_send}")

    # 3. Generate Content (Pollination AI + Cleaning)
    title, caption = get_pollination_text(video_to_send)
    
    # Note: Caption mein hi keywords included honge but bina # ke (kyunki user ne mana kiya hai)
    full_message = f"{title}\n\n{caption}"
    
    print(f"Generated Title: {title}")
    print(f"Generated Caption: {caption}")

    # 4. Send to Telegram (VIDEO FILE)
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("Sending Video File to Telegram...")
        with open(video_path, 'rb') as video_file:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID, 
                'caption': full_message
            }
            files = {'video': video_file}
            try:
                r = requests.post(url, data=payload, files=files)
                print(f"Telegram Status: {r.status_code}")
            except Exception as e:
                print(f"Telegram Error: {e}")

    # 5. Send to Webhook (VIDEO URL)
    if WEBHOOK_URL and GITHUB_REPO:
        print("Sending URL to Webhook...")
        # GitHub Raw URL Construction
        raw_video_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH_NAME}/{VIDEO_FOLDER}/{video_to_send}"
        # URL mein space agar ho to encode karo
        raw_video_url = raw_video_url.replace(" ", "%20")
        
        webhook_data = {
            "video_url": raw_video_url,
            "title": title,
            "caption": caption,
            "source": "GitHub Automation"
        }
        try:
            r = requests.post(WEBHOOK_URL, json=webhook_data)
            print(f"Webhook Status: {r.status_code}")
        except Exception as e:
            print(f"Webhook Error: {e}")

    # 6. Update History
    new_history.append({
        "filename": video_to_send,
        "date_sent": today.isoformat()
    })
    save_history(new_history)
    print("History updated.")

if __name__ == "__main__":
    run_automation()
