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

# --- SEO HASHTAGS ---
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

# --- HUMAN & AD LOGIC ---

def check_and_close_ads(driver):
    """
    Logic: Agar Ad aaya to close karo, nahi aaya to ignore karo.
    """
    try:
        # Check karte hain ki kitne tabs khule hain
        if len(driver.window_handles) > 1:
            print("🚫 Ad/Popup Detected! Closing it now...")
            
            # Ad wale tab par jao
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(0.5) # Thoda ruko
            driver.close()    # Band karo
            
            # Wapas Main Tab par aao
            driver.switch_to.window(driver.window_handles[0])
            print("✅ Ad Closed. Back to work.")
        else:
            # Agar koi Ad nahi hai, to chupchap aage badho
            pass
    except Exception as e:
        print(f"⚠️ Ad Handle Error (Ignored): {e}")

def human_sleep(min_t=1.5, max_t=3.5):
    time.sleep(random.uniform(min_t, max_t))

def human_scroll(driver):
    print("👀 Scrolling page like a human...")
    try:
        scroll_height = random.randint(300, 700)
        driver.execute_script(f"window.scrollTo(0, {scroll_height});")
        time.sleep(random.uniform(1.0, 2.5))
        driver.execute_script(f"window.scrollBy(0, {random.randint(100, 300)});")
        time.sleep(random.uniform(1.0, 2.0))
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(random.uniform(0.5, 1.5))
    except: pass

def human_click(driver, element):
    try:
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        time.sleep(random.uniform(0.5, 1.2))
        actions.click(element).perform()
    except:
        element.click()

def clean_caption(raw_text):
    if not raw_text: return "New Reel"
    clean_text = re.sub(r'#\w+', '', raw_text)
    return clean_text.strip()

def download_via_sssinstagram(insta_link):
    print("🕵️ Launching Browser...")
    
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={ua}")
    
    # Version 144 Fix
    driver = uc.Chrome(options=options, version_main=144)
    
    video_path = "final_video.mp4"
    processed_caption = "New Reel" 
    
    try:
        print("🌍 Opening SSSInstagram...")
        driver.get("https://sssinstagram.com/")
        
        # Check Ad (Website khulte hi)
        check_and_close_ads(driver)
        
        human_sleep(2, 4)
        human_scroll(driver)

        print("✍️ Finding Input Box...")
        try:
            input_box = driver.find_element(By.ID, "main_page_text")
        except:
            input_box = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Paste']")
            
        human_click(driver, input_box)
        
        # Typing logic
        input_box.send_keys(insta_link)
        human_sleep(0.5, 1.5)
        
        # Check Ad (Link paste karne ke baad)
        check_and_close_ads(driver)

        print("🖱️ Clicking Download...")
        try:
            submit_btn = driver.find_element(By.ID, "submit")
            human_click(driver, submit_btn)
        except:
            input_box.send_keys(Keys.ENTER)
            
        # Check Ad (Button dabane ke baad - Sabse important)
        human_sleep(2, 3) # Thoda ruko taaki Ad load ho jaye agar aana ho
        check_and_close_ads(driver)
        
        print("⏳ Waiting for Result...")
        try:
            download_btn = WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.CLASS_NAME, "download_link"))
            )
        except:
            download_btn = WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Download') and contains(@href, 'http')]"))
            )

        # Check Ad (Final download se pehle)
        check_and_close_ads(driver)
        
        driver.execute_script("arguments[0].scrollIntoView();", download_btn)
        human_sleep(1, 2)

        video_url = download_btn.get_attribute("href")
        print(f"🔗 Link Found: {video_url[:50]}...")
        
        # Caption Extract
        try:
            p_tags = driver.find_elements(By.XPATH, "//div[contains(@class, 'result')]//p")
            raw_caption = ""
            for p in p_tags:
                text = p.text
                if len(text) > 5 and "Download" not in text:
                    raw_caption = text
                    break
            if raw_caption:
                processed_caption = clean_caption(raw_caption)
        except: pass

        if not video_url: raise Exception("Video URL Not Found")

        print("⬇️ Downloading File...")
        headers = {"User-Agent": ua} 
        r = requests.get(video_url, headers=headers, stream=True)
        
        with open(video_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
        
        file_size = os.path.getsize(video_path)
        print(f"📁 File Size: {file_size} bytes")
        
        if file_size < 50000:
             raise Exception("File too small (Possible Ad Block).")

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
    final_caption = f"{clean_text}\n.\n.\n.\n.\n.\n{SEO_HASHTAGS}"
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "video": video_url,
                "caption": final_caption
            }
            requests.post(api_url, json=payload)
        except: pass

    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={
                "video_url": video_url, 
                "caption": final_caption,
                "raw_caption": clean_text,
                "source": original_link
            })
        except: pass

def update_history(link):
    with open(HISTORY_FILE, 'a') as f: f.write(link + "\n")

if __name__ == "__main__":
    if not WEBHOOK_URL:
        print("❌ ERROR: Webhook URL is REQUIRED.")
    
    link = get_next_link()
    if link:
        print(f"🎯 Processing: {link}")
        video_file, clean_text = download_via_sssinstagram(link)
        
        if video_file and os.path.exists(video_file):
            catbox_link = upload_to_catbox(video_file)
            if catbox_link:
                print(f"✅ Success: {catbox_link}")
                send_notification(catbox_link, clean_text, link)
                update_history(link)
                os.remove(video_file)
                print("✅ All Done!")
            else:
                print("❌ Upload Failed.")
        else:
            print("❌ Download Failed.")
            exit(1)
    else:
        print("💤 No new links.")
