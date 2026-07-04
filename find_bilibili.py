import urllib.parse
import requests
import re
import json
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def get_bilibili_craft_videos():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.com/"
    }
    
    kws = ["手工DIY", "创意手工", "折纸教程"]
    for kw in kws:
        print(f"Searching Bilibili for: {kw}")
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
                            title = re.sub(r'<[^>]+>', '', v.get('title', ''))
                            play = v.get('play')
                            # Check if vertical (typically vertical videos on bilibili have lower height/width ratio or are short duration)
                            duration = v.get('duration')
                            video_url = f"https://www.bilibili.com/video/{bvid}"
                            print(f"URL: {video_url} | Title: {title} | Duration: {duration} | Play: {play}")
        except Exception as e:
            print(f"Error searching Bilibili for {kw}: {e}")

if __name__ == "__main__":
    get_bilibili_craft_videos()
