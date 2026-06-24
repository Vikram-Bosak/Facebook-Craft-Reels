import os
import json
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()
HISTORY_FILE = 'downloaded_history.txt'
QUEUE_FILE = 'workspace/queue.json'

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_to_history(video_id):
    with open(HISTORY_FILE, 'a') as f:
        f.write(f"{video_id}\n")

def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_queue(queue):
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2)

async def scan_douyin_food_videos():
    print("Scanning Douyin Food section for new videos...")
    history = load_history()
    queue = load_queue()
    queued_ids = {item['id'] for item in queue}
    
    # Target URL for food videos
    target_url = "https://www.douyin.com/jingxuan/food"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Extract cards with data-aweme-id
            cards = await page.query_selector_all('[data-aweme-id]')
            print(f"Found {len(cards)} video cards on the page.")
            
            new_candidates = []
            for card in cards:
                aweme_id = await card.get_attribute('data-aweme-id')
                if not aweme_id:
                    continue
                    
                if aweme_id in history or aweme_id in queued_ids:
                    continue
                    
                text = await card.inner_text()
                text_cleaned = ' '.join(text.split())
                
                # Check for food related keywords
                keywords = ["美食", "小吃", "烹饪", "做菜", "食谱", "味道", "烧烤", "海鲜", "水果", "夜市", "葱花饼", "牛肋排"]
                is_food = any(kw in text_cleaned for kw in keywords)
                
                if is_food:
                    video_url = f"https://www.douyin.com/video/{aweme_id}"
                    new_candidates.append({
                        "id": aweme_id,
                        "title": text_cleaned[:120],
                        "source_url": video_url,
                        "status": "PENDING"
                    })
                    print(f"Discovered new food video: ID={aweme_id} | Title={text_cleaned[:50]}")
            
            if new_candidates:
                # Add to queue
                queue.extend(new_candidates)
                save_queue(queue)
                print(f"Added {len(new_candidates)} new videos to the queue.")
            else:
                print("No new unique food videos discovered in this scan.")
                
        except Exception as e:
            print(f"Error scanning Douyin: {e}")
        finally:
            await browser.close()

async def extract_douyin_video_url(page_url):
    print(f"Extracting video URL from: {page_url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            viewport={'width': 375, 'height': 812},
            is_mobile=True,
            has_touch=True
        )
        page = await context.new_page()
        try:
            await page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            
            # Get video source
            video_src = None
            video_elements = await page.query_selector_all("video")
            for v in video_elements:
                src = await v.get_attribute("src")
                if src:
                    video_src = src
                    break
                    
            if not video_src:
                sources = await page.query_selector_all("video source")
                for s in sources:
                    src = await s.get_attribute("src")
                    if src:
                        video_src = src
                        break
                        
            if video_src:
                if video_src.startswith("//"):
                    video_src = "https:" + video_src
                elif video_src.startswith("/"):
                    video_src = "https://www.douyin.com" + video_src
                print(f"Extracted video source URL: {video_src}")
                return video_src
        except Exception as e:
            print(f"Error extracting video URL: {e}")
        finally:
            await browser.close()
    return None

def download_video_direct(video_url, output_path):
    print(f"Downloading video to {output_path}...")
    import requests
    headers = {
        "Referer": "https://www.douyin.com/",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if os.path.exists(output_path):
            os.remove(output_path)
            
        response = requests.get(video_url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"Video downloaded successfully ({os.path.getsize(output_path)} bytes)")
            return True
        return False
    except Exception as e:
        print(f"Error downloading video: {e}")
        return False

def run_downloader():
    print("Running Downloader: Scanning and filling queue...")
    asyncio.run(scan_douyin_food_videos())
    
    # Return the first PENDING video in the queue if available
    queue = load_queue()
    pending = [item for item in queue if item['status'] == 'PENDING']
    if pending:
        item = pending[0]
        print(f"Next pending video: {item['title']} ({item['source_url']})")
        
        # Extract and download the video
        video_url = asyncio.run(extract_douyin_video_url(item['source_url']))
        if video_url:
            local_path = os.path.abspath("workspace/raw_video.mp4")
            if download_video_direct(video_url, local_path):
                item['local_path'] = local_path
                item['status'] = 'DOWNLOADED'
                item['download_status'] = 'Success'
                # Update status in queue
                for q_item in queue:
                    if q_item['id'] == item['id']:
                        q_item['status'] = 'DOWNLOADED'
                save_queue(queue)
                return item
        item['download_status'] = 'Failed'
        return item
    return None

if __name__ == "__main__":
    item = run_downloader()
    if item:
        # Write to state files for sequential running
        os.makedirs("workspace", exist_ok=True)
        with open("workspace/video_data.json", "w") as f:
            json.dump(item, f, indent=2)
        
        report_data = {
            "video_name": item.get("title", "N/A"),
            "download_status": item.get("download_status", "Failed"),
            "editing_status": "N/A",
            "upload_status": "N/A",
            "seo_title": "N/A",
            "description": "N/A",
            "facebook_url": "N/A",
            "youtube_url": "N/A"
        }
        with open("workspace/report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        print("Downloader finished and saved state.")
    else:
        print("No video to download.")

