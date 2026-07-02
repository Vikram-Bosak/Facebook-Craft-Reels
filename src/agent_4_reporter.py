import os
import json
import requests
import shutil
import html

def send_discord_webhook(message):
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("Discord Webhook configuration is missing. Skipping Discord notification.")
        return False
        
    # Clean HTML tags for Discord Markdown style compatibility
    clean_message = message.replace("<b>", "**").replace("</b>", "**")
    
    payload = {
        "content": clean_message
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=30)
        response.raise_for_status()
        print("Successfully sent Discord report.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Discord message: {e}")
        return False

def main():
    print("Starting Agent 4: Reporter")
    report_path = "workspace/report.json"
    
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            try:
                report = json.load(f)
            except json.JSONDecodeError:
                report = {}
    else:
        report = {}
        
    # Default values in case keys are missing (HTML-escaped for safety)
    video_name = html.escape(report.get('video_name', 'N/A'))
    download_status = html.escape(report.get('download_status', 'Failed / Unknown'))
    editing_status = html.escape(report.get('editing_status', 'N/A'))
    upload_status = html.escape(report.get('upload_status', 'N/A'))
    seo_title = html.escape(report.get('seo_title', 'N/A'))
    description = html.escape(report.get('description', 'N/A'))
    
    # Get FB and YT URLs with support for both format styles
    fb_url = html.escape(report.get('facebook_url', report.get('fb_url', 'N/A')))
    yt_url = html.escape(report.get('youtube_url', report.get('yt_url', 'N/A')))
    
    # Determine YouTube Status
    yt_status = "Success" if "youtube.com" in yt_url or "youtu.be" in yt_url else "Failed / N/A"
    
    # GitHub Action Variables
    repo = os.environ.get('GITHUB_REPOSITORY', 'Facebook-Viral-Chinese-Reels')
    run_id = os.environ.get('GITHUB_RUN_ID', 'UNKNOWN')
    repo_url = f"https://github.com/{repo}"
    run_url = f"{repo_url}/actions/runs/{run_id}"
    
    emoji_status = "✅" if upload_status == "Success" else "❌"
    
    yt_status_label = "Success" if yt_status == "Success" else "Failed"
    
    message = (
        f"{emoji_status} <b>📤 Pipeline Run Complete</b>\n\n"
        f"🎬 <b>Video Name:</b>\n{video_name}\n\n"
        f"📥 <b>Download Status:</b> {download_status}\n"
        f"✂️ <b>Editing Status:</b> {editing_status}\n"
        f"📤 <b>Facebook Upload:</b> {upload_status}\n"
        f"📤 <b>YouTube Upload:</b> {yt_status_label}\n\n"
        f"🏷️ <b>SEO Title:</b>\n{seo_title}\n\n"
        f"📝 <b>Description:</b>\n{description}\n\n"
        f"🔗 <b>Facebook Reel:</b>\n{fb_url}\n\n"
        f"▶️ <b>YouTube Video:</b>\n{yt_url}\n\n"
        f"📦 <b>GitHub Repo:</b>\n{repo_url}\n\n"
        f"📄 <b>Workflow Run:</b>\n{run_url}"
    )
    
    if "No new video" in download_status:
        print("No new video to process. Skipping Discord notification.")
    else:
        send_discord_webhook(message)
    
    # Selective Cleanup to preserve queue.json and processed_history.json
    print("Performing selective cleanup of temporary files in workspace...")
    temp_files = [
        "workspace/video_data.json",
        "workspace/report.json",
        "workspace/raw_video.mp4"
    ]
    for tf in temp_files:
        if os.path.exists(tf):
            try:
                os.remove(tf)
                print(f"Removed temporary file: {tf}")
            except Exception as e:
                print(f"Could not remove {tf}: {e}")
                
    if os.path.exists("workspace"):
        for filename in os.listdir("workspace"):
            if filename.startswith("edited_") or filename.startswith("raw_video"):
                filepath = os.path.join("workspace", filename)
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                        print(f"Removed temporary file: {filepath}")
                except Exception as e:
                    print(f"Could not remove {filepath}: {e}")

if __name__ == "__main__":
    main()

