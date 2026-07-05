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

async def scan_douyin_craft_videos():
    print("Scanning Douyin DIY/Craft section for new videos...")
    history = load_history()
    queue = load_queue()
    queued_ids = {item['id'] for item in queue}
    
    # Target URL for DIY/Craft videos
    target_url = "https://www.douyin.com/jingxuan/diy"
    
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
                
                # Check for craft/DIY related keywords (handmade, origami, clay, carving, woodworking, knitting, drawing, etc.)
                keywords = [
                    "手工", "手艺", "DIY", "折纸", "黏土", "雕刻", "编织", "木工", "画画", "手工制作", "创意手工", "废物利用", "工艺品", "纸艺", "旧物改造", "生活妙招"
                ]
                is_craft = any(kw in text_cleaned for kw in keywords)
                
                if is_craft:
                    video_url = f"https://www.douyin.com/video/{aweme_id}"
                    new_candidates.append({
                        "id": aweme_id,
                        "title": text_cleaned[:120],
                        "source_url": video_url,
                        "status": "PENDING"
                    })
                    print(f"Discovered new craft video: ID={aweme_id} | Title={text_cleaned[:50]}")
            
            if new_candidates:
                # Add to queue
                queue.extend(new_candidates)
                save_queue(queue)
                print(f"Added {len(new_candidates)} new videos to the queue.")
            else:
                print("No new unique craft videos discovered in this scan.")
                
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

def is_9_16_ratio(video_path):
    import subprocess
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'json', video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        info = json.loads(result.stdout)
        streams = info.get('streams', [])
        if not streams:
            return False
        width = streams[0].get('width')
        height = streams[0].get('height')
        if not width or not height:
            return False
        ratio = width / height
        print(f"Video dimensions: {width}x{height}, Aspect Ratio: {ratio:.4f}")
        # 9:16 is exactly 0.5625. Allow range 0.55 to 0.58
        return 0.55 <= ratio <= 0.58
    except Exception as e:
        print(f"Error checking aspect ratio: {e}")
        return False

def scan_bilibili_craft_videos():
    import urllib.parse
    import requests
    import re
    
    print("Scanning Bilibili DIY/Craft section for new videos...")
    history = load_history()
    queue = load_queue()
    queued_ids = {item['id'] for item in queue}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/"
    }
    
    new_candidates = []
    kws = ["手工DIY", "创意手工", "折纸教程"]
    for kw in kws:
        try:
            url = f"https://api.bilibili.com/x/web-interface/wbi/search/all/v2?keyword={urllib.parse.quote(kw)}"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('code') == 0:
                    result = data.get('data', {}).get('result', [])
                    video_result = None
                    if isinstance(result, list):
                        for item in result:
                            if isinstance(item, dict) and item.get('result_type') == 'video':
                                video_result = item
                                break
                    elif isinstance(result, dict):
                        video_result = result.get('video')
                        
                    if video_result:
                        data_list = video_result.get('data', [])
                        for v in data_list:
                            bvid = v.get('bvid')
                            if not bvid:
                                continue
                            if bvid in history or bvid in queued_ids:
                                continue
                                
                            duration_str = v.get('duration', '0:0')
                            parts = duration_str.split(':')
                            duration_sec = 0
                            if len(parts) == 2:
                                duration_sec = int(parts[0]) * 60 + int(parts[1])
                            elif len(parts) == 3:
                                duration_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                
                            # We only want short reels (<= 90 seconds)
                            if duration_sec > 90 or duration_sec < 10:
                                continue
                                
                            title = re.sub(r'<[^>]+>', '', v.get('title', ''))
                            video_url = f"https://www.bilibili.com/video/{bvid}"
                            
                            new_candidates.append({
                                "id": bvid,
                                "title": title,
                                "source_url": video_url,
                                "status": "PENDING"
                            })
                            print(f"Discovered new Bilibili craft video: ID={bvid} | Title={title[:50]} | Duration={duration_str}")
        except Exception as e:
            print(f"Error scanning Bilibili for {kw}: {e}")
            
    if new_candidates:
        queue.extend(new_candidates)
        save_queue(queue)
        print(f"Added {len(new_candidates)} new Bilibili videos to the queue.")
    else:
        print("No new unique Bilibili videos discovered in this scan.")

def run_downloader():
    print("Running Downloader: Scanning and filling queue...")
    asyncio.run(scan_douyin_craft_videos())
    scan_bilibili_craft_videos()
    
    # Loop to find the first PENDING video in the queue that has a 9:16 aspect ratio
    queue = load_queue()
    while True:
        pending = [item for item in queue if item['status'] == 'PENDING']
        if not pending:
            print("No pending videos left in the queue.")
            return None
            
        item = pending[0]
        print(f"Next pending video: {item['title']} ({item['source_url']})")
        
        # Extract and download the video
        local_path = os.path.abspath("workspace/raw_video.mp4")
        download_success = False
        
        if "bilibili.com" in item['source_url']:
            print(f"Downloading Bilibili video: {item['source_url']}")
            # Add sys.path to find download_bilibili
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from download_bilibili import download_bilibili_video
            download_success = asyncio.run(download_bilibili_video(item['source_url'], local_path))
        else:
            print(f"Downloading Douyin video: {item['source_url']}")
            video_url = asyncio.run(extract_douyin_video_url(item['source_url']))
            if video_url:
                download_success = download_video_direct(video_url, local_path)
        
        if download_success:
            # Verify aspect ratio is 9:16
            if is_9_16_ratio(local_path):
                item['local_path'] = local_path
                item['status'] = 'DOWNLOADED'
                item['download_status'] = 'Success'
                # Update status in queue
                for q_item in queue:
                    if q_item['id'] == item['id']:
                        q_item['status'] = 'DOWNLOADED'
                save_queue(queue)
                return item
            else:
                print(f"Skipping video ID={item['id']} because aspect ratio is not 9:16.")
                item['status'] = 'SKIPPED_ASPECT_RATIO'
                item['download_status'] = 'Skipped (Not 9:16)'
                for q_item in queue:
                    if q_item['id'] == item['id']:
                        q_item['status'] = 'SKIPPED_ASPECT_RATIO'
                save_queue(queue)
                if os.path.exists(local_path):
                    os.remove(local_path)
                continue  # try the next video in the queue
                    
        item['download_status'] = 'Failed'
        item['status'] = 'FAILED'
        for q_item in queue:
            if q_item['id'] == item['id']:
                q_item['status'] = 'FAILED'
        save_queue(queue)
        continue


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
            "youtube_url": "N/A",
            "source_url": item.get("source_url", "N/A")
        }
        with open("workspace/report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        print("Downloader finished and saved state.")
    else:
        print("No video to download.")

