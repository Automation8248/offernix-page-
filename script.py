import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os
import requests
import re

# --- SETTINGS ---
LINKS_FILE = "links.txt"
HISTORY_FILE = "history.txt"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- SEO TAGS ---
SEO_HASHTAGS = "#trending #viral #instagram #reels #explore #love #instagood #fashion #reelitfeelit #fyp #india #motivation"

def get_next_link():
    """History check karke naya link dhundta hai"""
    if not os.path.exists(LINKS_FILE): return None
    if not os.path.exists(HISTORY_FILE): 
        with open(HISTORY_FILE, 'w') as f: pass

    with open(LINKS_FILE, 'r') as f:
        all_links = [l.strip() for l in f.readlines() if l.strip()]
    with open(HISTORY_FILE, 'r') as f:
        history = [l.strip() for l in f.readlines()]

    for link in all_links:
        if link not in history: return link
    return None

def kill_ads(driver):
    """Ad Popups ko turant band karta hai"""
    try:
        if len(driver.window_handles) > 1:
            print("🚫 Ad Popup Detected! Closing...")
            driver.switch_to.window(driver.window_handles[1])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    except: pass

def clean_caption_text(raw_text):
    """Purane hashtags hatata hai"""
    if not raw_text: return "New Reel"
    # Regex se #tag hatao
    text = re.sub(r'#\w+', '', raw_text)
    return text.strip()

def download_video(insta_link):
    print("🚀 Launching Browser...")
    options = uc.ChromeOptions()
    options.add_argument("--headless=new") # Background mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    driver = uc.Chrome(options=options, version_main=None)
    video_path = "final_video.mp4"
    final_caption = "Reel"

    try:
        print("🌍 Opening SSSInstagram...")
        driver.get("https://sssinstagram.com/")
        time.sleep(3)

        # Input Box Logic
        try:
            input_box = driver.find_element(By.ID, "main_page_text")
        except:
            input_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Paste']")
            
        input_box.click()
        input_box.send_keys(insta_link)
        kill_ads(driver)

        # Download Click
        print("🖱️ Clicking Download...")
        try:
            driver.find_element(By.ID, "submit").click()
        except:
            input_box.send_keys(Keys.ENTER)
        
        kill_ads(driver)
        print("⏳ Waiting for Link...")

        # Robust Wait (15 seconds)
        try:
            download_btn = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "download_link"))
            )
        except:
            # Fallback agar class name change ho
            download_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
            )

        kill_ads(driver)
        video_url = download_btn.get_attribute("href")
        
        # Caption Extraction
        try:
            p_tags = driver.find_elements(By.XPATH, "//div[contains(@class, 'result')]//p")
            raw_text = ""
            for p in p_tags:
                if len(p.text) > 5 and "Download" not in p.text:
                    raw_text = p.text
                    break
            if raw_text:
                final_caption = clean_caption_text(raw_text)
        except: pass

        print("⬇️ Downloading File...")
        r = requests.get(video_url, stream=True)
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)

        # File Check
        if os.path.getsize(video_path) < 50000:
            raise Exception("File too small (Error Page)")

        return video_path, final_caption

    except Exception as e:
        print(f"❌ Error: {e}")
        driver.save_screenshot("error_debug.png")
        return None, None
    finally:
        driver.quit()

def upload_catbox(path):
    print("☁️ Uploading to Cloud...")
    try:
        with open(path, "rb") as f:
            r = requests.post("https://catbox.moe/user/api.php", 
                            data={"reqtype": "fileupload"}, 
                            files={"fileToUpload": f})
            if r.status_code == 200: return r.text.strip()
    except: pass
    return None

def notify(video_url, caption_text, source_link):
    # Caption Format: Text -> Dots -> SEO Tags
    formatted_msg = f"{caption_text}\n.\n.\n.\n.\n.\n{SEO_HASHTAGS}"

    # 1. Telegram Video
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("📨 Sending to Telegram...")
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "video": video_url,
                "caption": formatted_msg
            }
        )

    # 2. Webhook
    if WEBHOOK_URL:
        print("📨 Sending to Webhook...")
        requests.post(WEBHOOK_URL, json={
            "video_url": video_url,
            "caption": formatted_msg,
            "source": source_link
        })

if __name__ == "__main__":
    print("🎬 Bot Started...")
    link = get_next_link()
    
    if link:
        print(f"🔗 Processing: {link}")
        v_path, txt = download_video(link)
        
        if v_path:
            c_link = upload_catbox(v_path)
            if c_link:
                notify(c_link, txt, link)
                # History Update
                with open(HISTORY_FILE, 'a') as f: f.write(link + "\n")
                os.remove(v_path)
                print("✅ Task Completed!")
            else:
                print("❌ Upload Failed")
        else:
            print("❌ Download Failed")
            exit(1)
    else:
        print("💤 No New Links.")
