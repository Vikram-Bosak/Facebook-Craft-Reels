import os
import sys
import json
import subprocess
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from facebook_uploader import upload_reel
from agent_4_reporter import send_discord_webhook
from logger import logger

def main():
    load_dotenv()
    
    if len(sys.argv) < 2:
        print("Usage: python manual_run.py <Bilibili_or_Douyin_URL>")
        sys.exit(1)
        
    url = sys.argv[1]
    video_path = "output_dubbed_reel.mp4"
    workspace_dir = "workspace"
    
    # 1. Clean workspace directory
    print("Step 1: Cleaning workspace...")
    if os.path.exists(workspace_dir):
        for filename in os.listdir(workspace_dir):
            if filename != "raw_video.mp4":
                file_path = os.path.join(workspace_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception:
                    pass

    # 2. Download Bilibili video
    print(f"\nStep 2: Downloading video from: {url}")
    python_exe = sys.executable
    download_cmd = [python_exe, "download_bilibili.py", url]
    res_dl = subprocess.run(download_cmd)
    if res_dl.returncode != 0:
        print("Error: Video download failed.")
        sys.exit(1)

    # 3. Run translation pipeline
    print("\nStep 3: Running translation and dubbing pipeline...")
    pipeline_cmd = [python_exe, "run_pipeline.py", "mock_url"]
    res_pipe = subprocess.run(pipeline_cmd)
    if res_pipe.returncode != 0:
        print("Error: Translation pipeline failed.")
        sys.exit(1)

    # 4. Upload to Facebook Page
    print("\nStep 4: Uploading to Facebook Page...")
    caption = "Folds a Minecraft Creeper out of one piece of paper! ✂️🎨 Mind-blowing DIY Paper Craft! #diy #minecraft #creeper #papercraft #origami #shorts #craft"
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    try:
        fb_url = upload_reel(video_path, caption)
        print(f"Success: Reel uploaded to Facebook! Link: {fb_url}")
    except Exception as e:
        print(f"Error uploading to Facebook: {e}")
        sys.exit(1)

    # 5. Trigger Discord Report
    print("\nStep 5: Sending final report to Discord...")
    report_data = {
        "video_name": "一张纸竟折出苦力怕！！！ (Minecraft Creeper)",
        "download_status": "Success",
        "editing_status": "Success",
        "upload_status": "Success",
        "seo_title": "Folds a Minecraft Creeper out of one piece of paper!",
        "description": caption,
        "facebook_url": fb_url,
        "youtube_url": "N/A",
        "source_url": url
    }
    os.makedirs(workspace_dir, exist_ok=True)
    with open(os.path.join(workspace_dir, "report.json"), "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    reporter_script = os.path.join("src", "agent_4_reporter.py")
    res_rep = subprocess.run([python_exe, reporter_script])
    if res_rep.returncode == 0:
        print("Discord report sent successfully via Agent 4!")
    else:
        print("Failed to send Discord report.")

if __name__ == "__main__":
    main()
