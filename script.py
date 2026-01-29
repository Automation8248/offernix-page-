import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import os
import requests
import re

# --- CONFIGURATION ---
LINKS_FILE = "links.txt"
HISTORY_FILE = "history.txt"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- CAPTION SETTINGS ---
# Aapki demand: #aarvi aur SEO tags
CUSTOM_TAG = "#aarvi"
SEO_HASHTAGS = "#trending #viral #instagram #reels #explore #love #instagood #fashion #reelitfeelit #fyp #india #motivation"

def get_next_link():
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

# --- AD & HUMAN LOGIC ---

def check_and_close_ads(driver):
    """
    Agar naya tab/window khula (Ad) to use close karke main tab par wapas aao.
    """
    try:
        current_window = driver.current_window_handle
        all_windows = driver.window_handles
        
        if len(all_windows) > 1:
            print("🚫 Ad/Popup Detected! Closing/Cutting it...")
            for window in all_windows:
                if window != current_window:
                    driver.switch_to.window(window)
                    driver.close()
            driver.switch_to.window(current_window)
            print("✅ Ad Closed. Resuming work.")
    except Exception as e:
        print(f"⚠️ Ad Handler: {e}")

def human_sleep(min_t=1.0, max_t=3.0):
    """Random wait to mimic human thinking"""
    time.sleep(random.uniform(min_t, max_t))

def human_scroll(driver):
    """Thoda scroll karo taaki lage user content dekh raha hai"""
    print("👀 Scrolling page...")
    try:
        driver.execute_script(f"window.scrollBy(0, {random.randint(200, 500)});")
        time.sleep(random.uniform(1.0, 2.0))
        driver.execute_script("window.scrollTo(0, 0);") # Wapas upar aao input ke liye
    except: pass

def human_click(driver, element):
    """Mouse move karke click karna (Hover effect)"""
    try:
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        time.sleep(random.uniform(0.3, 0.8)) # Thoda ruko button ke upar
        actions.click(element).perform()
    except:
        element.click()

def clean_caption(raw_text):
    if not raw_text: return "New Reel"
    # Remove old hashtags
    clean_text = re.sub(r'#\w+', '', raw_text)
    return clean_text.strip()

def download_via_sssinstagram(insta_link):
    print("🕵️ Launching Browser...")
    
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # User Agent Identity (Important for download)
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={ua}")
    
    # Version Fix (Jo pehle kiya tha)
    driver = uc.Chrome(options=options, version_main=144)
    
    video_path = "final_video.mp4"
    processed_caption = "New Reel" 
    
    try:
        print("🌍 Opening SSSInstagram...")
        driver.get("https://sssinstagram.com/")
        
        # 1. Ad Check (Shuruat mein)
        check_and_close_ads(driver)
        human_sleep(2, 3)
        
        # 2. Find Input Box
        print("✍️ Pasting Link...")
        try:
            input_box = driver.find_element(By.ID, "main_page_text")
        except:
            input_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Paste']")
            
        human_click(driver, input_box)
        
        # 3. Direct Paste (No Typing Loop as requested)
        input_box.send_keys(insta_link)
        human_sleep(0.5, 1.0) # Paste karne ke baad thoda ruko
        
        # Ad Check after paste
        check_and_close_ads(driver)

        # 4. Click First 'Download' Button
        print("🖱️ Clicking First Download...")
        try:
            submit_btn = driver.find_element(By.ID, "submit")
            human_click(driver, submit_btn)
        except:
            input_box.send_keys(Keys.ENTER)
            
        # Ad Check immediately after click
        human_sleep(2, 4) 
        check_and_close_ads(driver)
        
        print("⏳ Waiting for Blue Download Button...")
        
        # 5. Wait for Result (Blue Button)
        # Screenshot mein 'Download' likha hai blue button par
        try:
            # Result container ke andar link dhundo
            download_btn = WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'download_link')]"))
            )
        except:
            # Backup locator
            download_btn = WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download')]"))
            )

        # Scroll to result (Human behavior)
        driver.execute_script("arguments[0].scrollIntoView();", download_btn)
        human_sleep(1, 2)
        
        # Get Direct Link (Click nahi karenge taki popup na aaye, seedha link uthayenge)
        video_url = download_btn.get_attribute("href")
        print(f"🔗 Video URL Found: {video_url[:50]}...")
        
        # 6. Extract Caption
        try:
            p_tags = driver.find_elements(By.XPATH, "//div[contains(@class, 'result')]//p")
            raw_caption = ""
            for p in p_tags:
                text = p.text
                # Ignore button text
                if len(text) > 5 and "Download" not in text:
                    raw_caption = text
                    break
            if raw_caption:
                processed_caption = clean_caption(raw_caption)
        except: pass

        if not video_url: raise Exception("Video URL Not Found")

        # 7. Download File (Requests ke through taaki safe rahe)
        print("⬇️ Downloading File...")
        
        # Headers zaroori hain taaki server block na kare (Fix for 'File too small')
        headers = {
            "User-Agent": ua,
            "Referer": "https://sssinstagram.com/"
        }
        
        r = requests.get(video_url, headers=headers, stream=True)
        
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
        
        file_size = os.path.getsize(video_path)
        print(f"📁 File Size: {file_size} bytes")
        
        # Size check (2KB se kam matlab error page)
        if file_size < 2000: 
             raise Exception("File too small (Download blocked or Error Page).")

        return video_path, processed_caption

    except Exception as e:
        print(f"❌ Browser Error: {e}")
        driver.save_screenshot("error_debug.png")
        return None, None
    finally:
        try:
            driver.quit()
        except: pass

def upload_to_catbox(file_path):
    print("☁️ Uploading to Catbox...")
    try:
        with open(file_path, "rb") as f:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.post("https://catbox.moe/user/api.php", 
                            data={"reqtype": "fileupload"}, 
                            files={"fileToUpload": f},
                            headers=headers)
            if r.status_code == 200: 
                return r.text.strip()
            else:
                return None
    except: return None

def send_notification(video_url, clean_text, original_link):
    print("🚀 Preparing Post...")
    
    # Caption: Text -> #aarvi -> SEO Hashtags
    final_caption = f"{clean_text}\n.\n.\n.\n.\n.\n{CUSTOM_TAG} {SEO_HASHTAGS}"
    
    # Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "video": video_url,
                "caption": final_caption
            }
            requests.post(api_url, json=payload)
            print("✅ Sent to Telegram")
        except Exception as e:
            print(f"❌ Telegram Fail: {e}")

    # Webhook
    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={
                "video_url": video_url, 
                "caption": final_caption,
                "raw_caption": clean_text,
                "source": original_link
            })
            print("✅ Sent to Webhook")
        except: pass

def update_history(link):
    with open(HISTORY_FILE, 'a') as f: f.write(link + "\n")

if __name__ == "__main__":
    link = get_next_link()
    if link:
        print(f"🎯 Processing: {link}")
        video_file, clean_text = download_via_sssinstagram(link)
        
        if video_file and os.path.exists(video_file):
            catbox_link = upload_to_catbox(video_file)
            if catbox_link:
                print(f"✅ Catbox Link: {catbox_link}")
                send_notification(catbox_link, clean_text, link)
                update_history(link)
                os.remove(video_file)
                print("✅ Task Completed Successfully!")
            else:
                print("❌ Catbox Upload Failed.")
        else:
            print("❌ Download Failed.")
            exit(1)
    else:
        print("💤 No new links.")
