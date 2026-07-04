import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Load env variables from .env
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from facebook_uploader import upload_reel
from logger import logger

def main():
    video_path = "output_dubbed_reel.mp4"
    if not os.path.exists(video_path):
        print(f"Error: {video_path} not found!")
        sys.exit(1)
        
    caption = "Folds a Minecraft Creeper out of one piece of paper! ✂️🎨 Mind-blowing DIY Paper Craft! #diy #minecraft #creeper #papercraft #origami #shorts #craft"
    
    print(f"Uploading {video_path} to Facebook Page...")
    try:
        url = upload_reel(video_path, caption)
        print("\n" + "="*50)
        print("🎉 SUCCESS: Reel uploaded to Facebook Page!")
        print(f"Facebook Video URL: {url}")
        print("="*50 + "\n")
    except Exception as e:
        print(f"Error uploading to Facebook: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
