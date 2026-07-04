import asyncio
import base64
import os
from playwright.async_api import async_playwright

async def download_via_eval_fetch(page_url, output_path):
    print(f"Opening browser for: {page_url}")
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
            await page.wait_for_selector("video", timeout=15000)
            
            video_src = await page.eval_on_selector("video", "el => el.src")
            if not video_src:
                # Try source tag
                video_src = await page.eval_on_selector("video source", "el => el.src")
                
            if video_src:
                if video_src.startswith("//"):
                    video_src = "https:" + video_src
                elif video_src.startswith("/"):
                    video_src = "https://www.douyin.com" + video_src
                    
                print(f"Found source: {video_src}. Fetching inside page context...")
                
                # Fetch inside the browser context to bypass CORS/403
                b64_data = await page.evaluate("""async (src) => {
                    const res = await fetch(src);
                    const buffer = await res.arrayBuffer();
                    let binary = '';
                    const bytes = new Uint8Array(buffer);
                    const len = bytes.byteLength;
                    for (let i = 0; i < len; i++) {
                        binary += String.fromCharCode(bytes[i]);
                    }
                    return btoa(binary);
                }""", video_src)
                
                if b64_data:
                    file_bytes = base64.b64decode(b64_data)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(file_bytes)
                    print(f"Downloaded successfully: {len(file_bytes)} bytes saved to {output_path}")
                    await browser.close()
                    return True
            else:
                print("No video source found.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()
    return False

if __name__ == "__main__":
    url = "https://www.douyin.com/video/7391863460088401186"
    asyncio.run(download_via_eval_fetch(url, "workspace/raw_video.mp4"))
