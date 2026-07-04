import asyncio
import json
import os
import re
import requests
import sys
import subprocess
from playwright.async_api import async_playwright

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

async def download_bilibili_video(url, output_path):
    print(f"Opening Bilibili to extract play info: {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Extract __playinfo__
            playinfo_str = await page.evaluate("() => JSON.stringify(window.__playinfo__)")
            if not playinfo_str or playinfo_str == "null":
                # Try finding in page source script tags
                content = await page.content()
                match = re.search(r'window\.__playinfo__\s*=\s*(\{.*?\});', content)
                if match:
                    playinfo_str = match.group(1)
                    
            if not playinfo_str:
                print("Could not find window.__playinfo__ on page.")
                await browser.close()
                return False
                
            playinfo = json.loads(playinfo_str)
            dash = playinfo.get('data', {}).get('dash')
            if not dash:
                print("Play info does not contain DASH streams.")
                await browser.close()
                return False
                
            video_url = dash.get('video', [{}])[0].get('baseUrl')
            audio_url = dash.get('audio', [{}])[0].get('baseUrl')
            
            if not video_url or not audio_url:
                print("Could not find video or audio baseUrl.")
                await browser.close()
                return False
                
            print("Extracted stream URLs successfully. Downloading streams...")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.bilibili.com/"
            }
            
            # Download video stream
            video_temp = "workspace/temp_video.m4s"
            audio_temp = "workspace/temp_audio.m4s"
            os.makedirs("workspace", exist_ok=True)
            
            print("Downloading video stream...")
            r_vid = requests.get(video_url, headers=headers, stream=True, timeout=60)
            r_vid.raise_for_status()
            with open(video_temp, 'wb') as f:
                for chunk in r_vid.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print("Downloading audio stream...")
            r_aud = requests.get(audio_url, headers=headers, stream=True, timeout=60)
            r_aud.raise_for_status()
            with open(audio_temp, 'wb') as f:
                for chunk in r_aud.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print("Merging streams using FFmpeg...")
            if os.path.exists(output_path):
                os.remove(output_path)
                
            cmd = [
                'ffmpeg', '-y',
                '-i', video_temp,
                '-i', audio_temp,
                '-c:v', 'copy',
                '-c:a', 'copy',
                output_path
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up temp files
            if os.path.exists(video_temp): os.remove(video_temp)
            if os.path.exists(audio_temp): os.remove(audio_temp)
            
            if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                print(f"Bilibili video downloaded successfully to {output_path} ({os.path.getsize(output_path)} bytes)")
                await browser.close()
                return True
            else:
                print(f"FFmpeg merging failed: {res.stderr}")
        except Exception as e:
            print(f"Error downloading: {e}")
        finally:
            await browser.close()
    return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.bilibili.com/video/BV17u411L7nP"
    out = "workspace/raw_video.mp4"
    asyncio.run(download_bilibili_video(url, out))
