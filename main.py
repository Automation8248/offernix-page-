import os
import requests
from dotenv import load_dotenv
from yt_dlp import YoutubeDL

# Environment Variables Load karein
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

VIDEO_DIR = "downloads"
os.makedirs(VIDEO_DIR, exist_ok=True)

# --- Helper Functions ---

def read_file(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return [x.strip() for x in f.readlines() if x.strip()]

def write_history(url):
    with open("history.txt", "a") as f:
        f.write(url + "\n")

def upload_video_robust(file_path):
    """
    Yeh function pehle Catbox try karega.
    Agar Catbox fail hua, toh File.io try karega.
    """
    # 1. Try Catbox
    try:
        print("🚀 Uploading to Catbox...")
        with open(file_path, "rb") as f:
            r = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f},
                timeout=120 # 2 minute timeout
            )
        if r.status_code == 200:
            return r.text.strip()
        else:
            print(f"⚠️ Catbox Error (Status {r.status_code}): {r.text}")
    except Exception as e:
        print(f"⚠️ Catbox Connection Failed: {e}")

    # 2. Try File.io (Backup)
    try:
        print("🔄 Switching to Backup (File.io)...")
        with open(file_path, "rb") as f:
            # Expires in 2 weeks (2w)
            r = requests.post("https://file.io/?expires=2w", files={"file": f}, timeout=120)
        
        if r.status_code == 200:
            return r.json().get("link")
        else:
            print(f"⚠️ File.io Error (Status {r.status_code}): {r.text}")
    except Exception as e:
        print(f"⚠️ File.io Connection Failed: {e}")

    # Agar dono fail ho gaye
    raise Exception("❌ All upload servers failed! Cannot proceed.")

# --- Main Logic ---

links = read_file("links.txt")
history = read_file("history.txt")

video_url = None
for link in links:
    if link not in history:
        video_url = link
        break

if not video_url:
    print("💤 No new video found to process.")
    exit()

# Try-Except Block (Poora process safe rakhne ke liye)
try:
    print(f"🎬 Processing: {video_url}")
    
    ydl_opts = {
        "outtmpl": f"{VIDEO_DIR}/video.%(ext)s",
        "format": "mp4",
        "quiet": True
    }

    # Step 1: Download
    print("⬇️ Downloading video...")
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        caption = info.get("description", "") or info.get("title", "")
        video_path = ydl.prepare_filename(info)

    if not os.path.exists(video_path):
        raise Exception("Download failed, file not found.")

    # Step 2: Upload (With Backup)
    final_video_link = upload_video_robust(video_path)
    print(f"✅ Upload Success: {final_video_link}")

    # Step 3: Send to Telegram
    print("✈️ Sending to Telegram...")
    telegram_api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    tg_resp = requests.post(
        telegram_api,
        data={
            "chat_id": CHAT_ID,
            "video": final_video_link,
            "caption": caption
        }
    )
    
    if tg_resp.status_code != 200:
        raise Exception(f"Telegram Failed: {tg_resp.text}")

    # Step 4: Send to Webhook
    if WEBHOOK_URL:
        print("🔗 Sending to Webhook...")
        wb_resp = requests.post(
            WEBHOOK_URL,
            json={"video_url": final_video_link}
        )
        if wb_resp.status_code != 200:
            print(f"⚠️ Webhook Warning: {wb_resp.text}") 
            # Webhook fail hone par history save rokna hai to neeche 'raise' uncomment karein:
            # raise Exception("Webhook Failed")

    # --- FINAL SUCCESS ---
    write_history(video_url)
    print("🎉 All Done! Link saved to history.")

    # Cleanup (Delete downloaded file)
    if os.path.exists(video_path):
        os.remove(video_path)
        print("🗑️ Temp file cleaned up.")

except Exception as e:
    print("\n------------------------------------------------")
    print(f"❌ PROCESS FAILED: {e}")
    print("⚠️ History was NOT updated. Will retry this link next time.")
    print("------------------------------------------------\n")
    # GitHub Actions ko fail dikhane ke liye exit code 1
    exit(1)
