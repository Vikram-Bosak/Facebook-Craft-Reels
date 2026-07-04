import requests
import sys

def send_video():
    token = "8891592804:AAE4m8wFAGreo0puMCXa61BISHgFUrBIhs0"
    chat_id = "6595054125"
    video_path = "output_dubbed_reel.mp4"
    
    url = f"https://api.telegram.org/bot{token}/sendVideo"
    
    print(f"Sending {video_path} to Telegram chat {chat_id}...")
    try:
        with open(video_path, 'rb') as f:
            files = {'video': f}
            data = {
                'chat_id': chat_id,
                'caption': 'Here is your edited and dubbed Minecraft Creeper craft video! ✂️🎨\n\n• Slower, more natural voice speed\n• Loofed BGM set to subtle 8% volume\n• Original sound effects preserved'
            }
            response = requests.post(url, data=data, files=files, timeout=120)
            res_json = response.json()
            if res_json.get('ok'):
                print("Video sent successfully via Telegram bot!")
                sys.exit(0)
            else:
                print(f"Failed to send video: {res_json}")
                sys.exit(1)
    except Exception as e:
        print(f"Error occurred while sending video: {e}")
        sys.exit(1)

if __name__ == "__main__":
    send_video()
