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
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY")
BRANCH_NAME = "main"

# --- HELPER FUNCTIONS ---

def clean_text(text):
    """
    Title aur Caption ke liye strict cleaner.
    Removes *, ., #, [], ()
    """
    if not text: return ""
    # Remove specific characters including hash inside title/caption
    cleaned = re.sub(r'[*\.#\[\]\(\)]', '', text)
    # Remove multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def get_affiliate_content(filename):
    """
    Pollination AI se Product-Based Content generate karega.
    Format: Title ||| Caption ||| Hashtags
    """
    clean_filename = filename.replace("_", " ").replace("-", " ").split(".")[0]
    
    # --- AFFILIATE MARKETING PROMPT ---
    # Hum AI ko bol rahe hain ki response ko '|||' se divide kare
    prompt = (
        f"Act as an expert affiliate marketer. "
        f"I have a product video file named '{clean_filename}'. "
        "1. Write a short, catchy, attention-grabbing product title (No emojis, No hashtags). "
        "2. Write a persuasive description/caption that says 'See this amazing unique product' or 'You need this gadget' (No emojis, No hashtags). "
        "3. Write 10 high-ranking SEO hashtags separated by spaces (Include # here). "
        "Output format strictly: Title ||| Caption ||| Hashtags"
    )
    
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://text.pollinations.ai/{encoded_prompt}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            raw_text = response.text
            
            # Response ko '|||' se split karte hain
            parts = raw_text.split('|||')
            
            if len(parts) >= 3:
                title_raw = parts[0]
                caption_raw = parts[1]
                hashtags_raw = parts[2]
            else:
                # Fallback agar AI ne format follow nahi kiya
                title_raw = f"Amazing Unique Product {clean_filename}"
                caption_raw = "Check out this useful gadget for your daily life It is very unique"
                hashtags_raw = "#gadgets #musthave #amazonfinds"

            # --- CLEANING ---
            # Title aur Caption mein se symbols hatayenge
            final_title = clean_text(title_raw)
            final_caption = clean_text(caption_raw)
            
            # Hashtags mein se brackets hatayenge par # rehne denge
            final_hashtags = re.sub(r'[\[\]\(\)\*\.]', '', hashtags_raw).strip()
            
            return final_title, final_caption, final_hashtags
        else:
            return clean_filename, "See this amazing product video", "#viral #product"
            
    except Exception as e:
        print(f"AI Generation Failed: {e}")
        return clean_filename, "See this amazing product video", "#viral #product"

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
    # 1. DELETE OLD FILES (15 Days Logic)
    history = load_history()
    today = datetime.date.today()
    new_history = []
    
    print("Checking for expired videos...")
    for entry in history:
        sent_date = datetime.date.fromisoformat(entry['date_sent'])
        days_diff = (today - sent_date).days
        
        file_path = os.path.join(VIDEO_FOLDER, entry['filename'])
        
        if days_diff >= 15:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"DELETED EXPIRED: {entry['filename']}")
        else:
            new_history.append(entry)
    
    save_history(new_history)
    history = new_history 

    # 2. PICK NEW VIDEO
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

    # 3. GENERATE AFFILIATE CONTENT
    title, caption, hashtags = get_affiliate_content(video_to_send)
    
    print(f"Title: {title}")
    print(f"Caption: {caption}")
    print(f"Tags: {hashtags}")

    # Telegram Message Format
    telegram_message = f"{title}\n\n{caption}\n\n{hashtags}"

    # 4. SEND TO TELEGRAM
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("Sending to Telegram...")
        with open(video_path, 'rb') as video_file:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID, 
                'caption': telegram_message
            }
            files = {'video': video_file}
            try:
                requests.post(url, data=payload, files=files)
            except Exception as e:
                print(f"Telegram Error: {e}")

    # 5. SEND TO WEBHOOK
    if WEBHOOK_URL and GITHUB_REPO:
        print("Sending to Webhook...")
        raw_video_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH_NAME}/{VIDEO_FOLDER}/{video_to_send}"
        raw_video_url = raw_video_url.replace(" ", "%20")
        
        webhook_data = {
            "video_url": raw_video_url,
            "title": title,
            "caption": caption,
            "hashtags": hashtags,
            "source": "AffiliateBot"
        }
        try:
            requests.post(WEBHOOK_URL, json=webhook_data)
        except Exception as e:
            print(f"Webhook Error: {e}")

    # 6. UPDATE HISTORY
    new_history.append({
        "filename": video_to_send,
        "date_sent": today.isoformat()
    })
    save_history(new_history)
    print("Automation Complete.")

if __name__ == "__main__":
    run_automation()
