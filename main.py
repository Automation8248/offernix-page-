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

# --- FIXED CAPTION & TAGS (Jo aapne diya hai) ---
PERMANENT_CAPTION = """New video post
.
.
.
.
.
#AffiliateMarketing #OnlineEarning #PassiveIncome #MakeMoneyOnline #EarnOnline #DigitalMarketing #InternetMarketing #SideIncome #SmartIncome #ProductReview #ProductVideo #BestProduct #TrendingProduct #TopDeals #MustBuy #UnboxingVideo #ProductDemo #HonestReview #WorthBuying #BuyNow #BestDeal #DiscountOffer #LimitedOffer #OfferAlert #SaleAlert #DealOfTheDay #OnlineShopping #BestPrice #ReelsIndia #InstaReels #ViralReels #TrendingReels #ExplorePage #YoutubeShorts #ShortsVideo #ViralVideo #IndianAffiliate #IndiaDeals #IndianProducts #DesiDeals"""

# --- HELPER FUNCTIONS ---

def clean_title(text):
    """
    Sirf Title ke liye: No *, ., #, [], ()
    """
    if not text: return ""
    # Remove specific characters
    cleaned = re.sub(r'[*\.#\[\]\(\)]', '', text)
    # Remove multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def get_ai_title(filename):
    """
    Pollination AI se sirf unique Title generate karega.
    """
    clean_filename = filename.replace("_", " ").replace("-", " ").split(".")[0]
    
    # Prompt: Explicitly asking to RENAME the product
    prompt = (
        f"Act as a copywriter. I have a video file named '{clean_filename}'. "
        "Write a short, catchy, 5-word product title for this. "
        "Do not use the exact filename. Make it sound like a hot new gadget or tool. "
        "Do not use hashtags or emojis in the title."
    )
    
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://text.pollinations.ai/{encoded_prompt}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            raw_title = response.text
            final_title = clean_title(raw_title)
            return final_title
        else:
            return f"Amazing New Product {clean_filename}"
    except Exception as e:
        print(f"AI Generation Failed: {e}")
        return f"Smart Gadget {clean_filename}"

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

    # 3. GENERATE TITLE ONLY
    generated_title = get_ai_title(video_to_send)
    
    # Combine Title + Fixed Caption
    full_caption_text = f"{generated_title}\n\n{PERMANENT_CAPTION}"
    
    print(f"Final Title: {generated_title}")

    # 4. SEND TO TELEGRAM
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("Sending to Telegram...")
        with open(video_path, 'rb') as video_file:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID, 
                'caption': full_caption_text
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
            "title": generated_title,
            "caption": PERMANENT_CAPTION,
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
