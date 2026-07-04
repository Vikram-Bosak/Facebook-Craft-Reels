import os
import sys
import shutil
import asyncio
import requests
from playwright.async_api import async_playwright

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Add src to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from logger import logger
from translator import translate_video

async def extract_douyin_video_url(page_url):
    logger.info(f"Opening browser with mobile user agent to extract video URL from: {page_url}")
    async with async_playwright() as p:
        # Emulate iPhone
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            viewport={'width': 375, 'height': 812},
            is_mobile=True,
            has_touch=True
        )
        page = await context.new_page()
        
        # Navigate
        await page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
        logger.info("Page loaded, waiting for video element...")
        
        # Wait up to 10 seconds for video tag
        try:
            await page.wait_for_selector("video", timeout=15000)
        except Exception as e:
            logger.warning(f"Timeout waiting for video tag: {e}")
            
        # Get video source
        video_src = None
        video_elements = await page.query_selector_all("video")
        for v in video_elements:
            src = await v.get_attribute("src")
            if src:
                video_src = src
                break
                
        # If not found directly on video, check source tags
        if not video_src:
            sources = await page.query_selector_all("video source")
            for s in sources:
                src = await s.get_attribute("src")
                if src:
                    video_src = src
                    break
                    
        if video_src:
            # Handle relative URL
            if video_src.startswith("//"):
                video_src = "https:" + video_src
            elif video_src.startswith("/"):
                video_src = "https://www.douyin.com" + video_src
            logger.info(f"Extracted video source URL: {video_src}")
            
            # Download directly using request context of Playwright to bypass 403 CDN blocks
            try:
                logger.info(f"Downloading video from CDN using browser session: {video_src}")
                response = await context.request.get(video_src, headers={
                    "Referer": "https://www.douyin.com/",
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
                })
                if response.status == 200:
                    body = await response.body()
                    os.makedirs("workspace", exist_ok=True)
                    with open("workspace/raw_video.mp4", "wb") as f:
                        f.write(body)
                    logger.info("Video downloaded successfully via Playwright context request.")
                    await browser.close()
                    return "workspace/raw_video.mp4"
                else:
                    logger.error(f"Download request failed with status: {response.status}")
            except Exception as e:
                logger.error(f"Failed to download via Playwright: {e}")
                
            await browser.close()
            return video_src
        else:
            await browser.close()
            logger.error("Could not find video element source.")
            return None

def download_video_direct(video_url, output_path):
    logger.info(f"Downloading video from CDN: {video_url}")
    headers = {
        "Referer": "https://www.douyin.com/",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }
    try:
        if os.path.exists(output_path):
            os.remove(output_path)
            
        response = requests.get(video_url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            logger.info(f"Video downloaded successfully to {output_path} ({os.path.getsize(output_path)} bytes)")
            return True
        else:
            logger.error("Download failed: file is empty or missing.")
            return False
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_pipeline.py <video_url>")
        sys.exit(1)
        
    url = sys.argv[1]
    workspace_dir = "workspace"
    os.makedirs(workspace_dir, exist_ok=True)
    
    raw_video = os.path.join(workspace_dir, "raw_video.mp4")
    
    # Check if video already downloaded to skip download step
    if os.path.exists(raw_video) and os.path.getsize(raw_video) > 1000000:
        logger.info(f"Using already downloaded video at: {raw_video}")
    elif "bilibili.com" in url:
        logger.info("Detected Bilibili URL. Downloading using yt-dlp...")
        import subprocess
        try:
            cmd = [
                sys.executable, "-m", "yt_dlp",
                url,
                "-o", raw_video,
                "--force-overwrites",
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode == 0 and os.path.exists(raw_video) and os.path.getsize(raw_video) > 1000:
                logger.info("Bilibili video downloaded successfully using yt-dlp.")
            else:
                logger.error(f"yt-dlp failed: {res.stderr}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Error running yt-dlp: {e}")
            sys.exit(1)
    else:
        # 1. Extract URL and download via Playwright context request
        video_url = asyncio.run(extract_douyin_video_url(url))
        if not video_url:
            logger.error("Failed to extract video. Exiting.")
            sys.exit(1)
            
        # If it downloaded directly, skip download_video_direct
        if video_url == "workspace/raw_video.mp4" and os.path.exists(raw_video):
            logger.info("Video successfully downloaded using browser context.")
        else:
            # 2. Download video (fallback)
            if not download_video_direct(video_url, raw_video):
                logger.error("Failed to download video file. Exiting.")
                sys.exit(1)
        
    # 3. Run translation pipeline
    logger.info("Starting translation & editing pipeline...")
    result = translate_video(
        raw_video,
        output_dir=workspace_dir,
        burn_subtitles=False,
        subtitle_language='english'
    )
    
    if result and result.get('english_video') and os.path.exists(result['english_video']):
        final_output = "output_dubbed_reel.mp4"
        shutil.copy2(result['english_video'], final_output)
        
        print("\n" + "="*50)
        print("🎉 SUCCESS: Chinese video downloaded, translated, and edited successfully!")
        print(f"Final English Video: {os.path.abspath(final_output)}")
        print(f"Subtitles: {result['subtitles']}")
        print("="*50 + "\n")
    else:
        logger.error("Failed to translate/edit video.")
        sys.exit(1)

if __name__ == '__main__':
    main()
