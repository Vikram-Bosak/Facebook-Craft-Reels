import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def download_video_via_intercept(page_url, output_path):
    print(f"Intercepting video from: {page_url}")
    # Enable autoplay without user interaction
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required", "--mute-audio"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            viewport={'width': 375, 'height': 812},
            is_mobile=True,
            has_touch=True
        )
        page = await context.new_page()
        
        video_chunks = {}
        
        async def handle_response(response):
            url = response.url
            content_type = response.headers.get("content-type", "")
            print(f"URL: {url[:100]} | Type: {content_type} | Status: {response.status}")
            if "video" in content_type or "mp4" in url or "douyinvod.com" in url or "octet-stream" in content_type:
                try:
                    body = await response.body()
                    if len(body) > 10000:
                        video_chunks[url] = body
                except Exception:
                    pass

        page.on("response", handle_response)
        
        try:
            await page.goto(page_url, wait_until="networkidle", timeout=60000)
            print("Page loaded, clicking page to ensure focus and start video playback...")
            # Click center of page to trigger play
            await page.mouse.click(187, 406)
            await page.wait_for_timeout(3000)
            # Try to force play via JS on all video elements
            await page.evaluate("() => { document.querySelectorAll('video').forEach(v => { v.muted = true; v.play(); }); }")
            print("Waiting 15 seconds for video to play and buffer...")
            await page.wait_for_timeout(15000)
        except Exception as e:
            print(f"Error during navigation: {e}")
        finally:
            await browser.close()
            
        if video_chunks:
            # Sort by size to get the largest chunk
            largest_url = max(video_chunks, key=lambda k: len(video_chunks[k]))
            largest_body = video_chunks[largest_url]
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(largest_body)
            print(f"Successfully saved video to {output_path} ({len(largest_body)} bytes)")
            return True
        else:
            print("No video chunks captured.")
            return False

if __name__ == "__main__":
    url = "https://www.douyin.com/video/7391863460088401186"
    out = "workspace/raw_video.mp4"
    asyncio.run(download_video_via_intercept(url, out))
