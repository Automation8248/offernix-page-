import os
import requests
from dotenv import load_dotenv
from yt_dlp import YoutubeDL

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

VIDEO_DIR = "downloads"
os.makedirs(VIDEO_DIR, exist_ok=True)

def read_file(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [x.strip() for x in f.readlines() if x.strip()]

def write_history(url):
    with open("history.txt", "a") as f:
        f.write(url + "\n")

links = read_file("links.txt")
history = read_file("history.txt")

video_url = None
for link in links:
    if link not in history:
        video_url = link
        break

if not video_url:
    print("No new video found")
    exit()

# --- MAIN PROCESS START ---
try:
    print(f"Processing: {video_url}")
    
    ydl_opts = {
        "outtmpl": f"{VIDEO_DIR}/video.%(ext)s",
        "format": "mp4",
        "quiet": True
    }

    # 1. Download Video
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        caption = info.get("description", "") or info.get("title", "")
        video_path = ydl.prepare_filename(info)

    # 2. Upload to Catbox
    print("Uploading to Catbox...")
    with open(video_path, "rb") as f:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": f}
        )
    
    # Check agar Catbox ne error diya
    if r.status_code != 200:
        raise Exception(f"Catbox Upload Failed: {r.text}")

    catbox_url = r.text.strip()
    print(f"Uploaded: {catbox_url}")

    # 3. Send to Telegram
    print("Sending to Telegram...")
    telegram_api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    tg_resp = requests.post(
        telegram_api,
        data={
            "chat_id": CHAT_ID,
            "video": catbox_url,
            "caption": caption
        }
    )
    
    # Check agar Telegram ne error diya
    if tg_resp.status_code != 200:
        raise Exception(f"Telegram Send Failed: {tg_resp.text}")

    # 4. Send to Webhook
    print("Sending to Webhook...")
    wb_resp = requests.post(
        WEBHOOK_URL,
        json={"video_url": catbox_url}
    )
    
    # Check agar Webhook ne error diya
    if wb_resp.status_code != 200:
        raise Exception(f"Webhook Failed: {wb_resp.text}")

    # --- SUCCESS ---
    # Sab kuch sahi raha to ab history save karenge
    write_history(video_url)
    print("✅ Work Success! Link saved to history.")

    # (Optional) Downloaded file delete kar do space bachane ke liye
    if os.path.exists(video_path):
        os.remove(video_path)

except Exception as e:
    # Agar kahin bhi error aaya to yahan aayega aur history save NAHI karega
    print(f"❌ Error occurred: {e}")
    print("⚠️ History not updated because the task failed.")
