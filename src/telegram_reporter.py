import os
import requests
from datetime import datetime

# Try local/package imports
try:
    from .common.telegram import send_message, get_run_details
    from .logger import logger
except ImportError:
    try:
        from common.telegram import send_message, get_run_details
        from logger import logger
    except ImportError:
        # Fallback in case paths are not fully resolved
        def send_message(message: str, chat_id: str = None) -> None:
            token = os.environ.get("TELEGRAM_BOT_TOKEN")
            chat = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
            if not token or not chat:
                print("Telegram missing config:", message)
                return
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(url, json={"chat_id": chat, "text": message, "parse_mode": "HTML"}, timeout=10)
        
        def get_run_details() -> str:
            run_id = os.environ.get("GITHUB_RUN_ID", "Local")
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"<b>Run ID:</b> {run_id}\n<b>Time:</b> {current_time}"
        
        class MockLogger:
            def info(self, msg): print(f"INFO: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
        logger = MockLogger()

def report_progress(step: str, detail: str = ""):
    """Sends a real-time progress update to Telegram."""
    logger.info(f"Progress Update: {step} - {detail}")
    msg = f"🔄 <b>Pipeline Progress</b>\n<b>Step:</b> {step}\n"
    if detail:
        msg += f"<b>Detail:</b> {detail}\n"
    msg += f"\n{get_run_details()}"
    send_message(msg)

def report_success(filename: str, title: str, fb_url: str, remaining_queue: int, media_type: str = "reel"):
    """Reports a successful upload to Telegram."""
    logger.info(f"Reporting success for {filename}")
    msg = (
        f"✅ <b>Upload Successful!</b>\n\n"
        f"🎬 <b>File:</b> {filename}\n"
        f"🏷️ <b>Title:</b> {title}\n"
        f"📦 <b>Type:</b> {media_type.upper()}\n"
        f"🔗 <b>Link:</b> {fb_url}\n"
        f"📋 <b>Remaining in Queue:</b> {remaining_queue}\n\n"
        f"{get_run_details()}"
    )
    send_message(msg)

def report_failure(filename: str, error_msg: str, remaining_queue: int, media_type: str = "reel"):
    """Reports a pipeline failure to Telegram."""
    logger.error(f"Reporting failure for {filename}: {error_msg}")
    msg = (
        f"❌ <b>Pipeline Failure!</b>\n\n"
        f"🎬 <b>File:</b> {filename}\n"
        f"📦 <b>Type:</b> {media_type.upper() if filename != 'System Health Check' else 'N/A'}\n"
        f"⚠️ <b>Error:</b> {error_msg}\n"
        f"📋 <b>Remaining in Queue:</b> {remaining_queue}\n\n"
        f"{get_run_details()}"
    )
    send_message(msg)
