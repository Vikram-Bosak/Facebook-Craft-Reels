import os
import sys

# Load env variables from .env
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from agent_4_reporter import send_discord_webhook

def main():
    video_name = "一张纸竟折出苦力怕！！！ (Minecraft Creeper)"
    upload_status = "Success"
    seo_title = "Folds a Minecraft Creeper out of one piece of paper!"
    description = "Folds a Minecraft Creeper out of one piece of paper! ✂️🎨 Mind-blowing DIY Paper Craft! #diy #minecraft #creeper #papercraft #origami #shorts #craft"
    raw_video_url = "https://www.bilibili.com/video/BV17u411L7nP"
    fb_url = "https://www.facebook.com/1193838070480425/videos/2462506767549398"
    yt_url = "N/A"
    
    message = (
        f"✅ Pipeline Run Completed\n\n"
        f"🎬 Video Name:\n{video_name}\n\n"
        f"📤 Facebook Upload Status: {upload_status}\n"
        f"📤 YouTube Upload Status: Failed / N/A\n\n"
        f"🏷️ SEO Title:\n{seo_title}\n\n"
        f"📝 Description:\n{description}\n\n"
        f"Original File: {video_name}\n\n"
        f"🔗 Raw Video URL:\n{raw_video_url}\n\n"
        f"🔗 Facebook Reel URL:\n{fb_url}\n\n"
        f"▶️ YouTube Video URL:\n{yt_url}"
    )
    
    print("Sending manual report to Discord webhook...")
    success = send_discord_webhook(message)
    if success:
        print("Report sent successfully!")
    else:
        print("Failed to send report.")

if __name__ == "__main__":
    main()
