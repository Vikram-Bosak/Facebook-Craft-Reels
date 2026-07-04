# 🇺🇸 AI US Audience Craft/DIY Video Automation System

Fully automated cloud-based system that uploads Chinese viral craft/DIY videos to Facebook Reels and YouTube Shorts, **auto-translated to English** for United States audience.

System runs 24/7, fetching Chinese craft videos, translating them to English, generating AI SEO titles, uploading, and sending reports via Telegram.

## ✨ Features

- **Chinese → English Translation**: Automatically translates Chinese videos with:
  - English AI voice dubbing (edge-tts)
  - Dual subtitles (Chinese + English)
  - Professional translation via OpenAI GPT
- **Google Drive Integration**: Automatically scans for new Chinese videos.
- **AI SEO Optimization**: English viral titles, descriptions, and hashtags for US audience.
- **US Peak Hours Scheduling**: Posts during US Eastern Time prime hours:
  - 🌅 Morning Commute: 7:00 - 9:00 AM EST
  - 🍜 Lunch Break: 12:00 - 1:00 PM EST
  - 🌙 Prime Time: 5:00 - 9:00 PM EST
- **Multi-Platform Upload**: Facebook Reels + YouTube Shorts simultaneously.
- **Telegram Reporting**: Instant notifications in English.
- **Duplicate Prevention & Database Sync**: SQLite tracking with Google Drive sync.
- **GitHub Actions**: Automated scheduling every 4 hours.

## 🛠️ Setup Instructions

### 1. Prerequisites

You need accounts/keys for:
- **Facebook Page**: To upload Reels (US audience page recommended).
- **Facebook Developer App**: For Graph API Access Token.
- **Google Cloud Console**: Service Account for Google Drive access.
- **Telegram Bot**: For notifications.
- **OpenAI API Key**: For translation and SEO generation.

### 2. Environment Variables & GitHub Secrets

Copy `.env.example` to `.env` for local testing.
For GitHub Actions, add these as **Repository Secrets**:

| Variable | Description |
|---|---|
| `FB_ACCESS_TOKEN` | Facebook Page Access Token (needs `pages_manage_posts`, `pages_read_engagement`) |
| `FB_PAGE_ID` | Your Facebook Page ID |
| `TELEGRAM_BOT_TOKEN` | Token from BotFather |
| `TELEGRAM_CHAT_ID` | Your Chat ID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Google Service Account key JSON string |
| `GOOGLE_DRIVE_FOLDER_ID` | Google Drive parent folder ID |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `ENABLE_TRANSLATION` | Set to `true` for Chinese→English translation |
| `TTS_VOICE` | English voice: `en-US-ChristopherNeural` (default) |

### 3. Google Drive Setup

1. Create a main folder (e.g., `Chinese-Videos-US`) and get its ID.
2. Share with your Service Account email (Editor access).
3. Script creates `Pending`, `Uploaded`, `Failed` subfolders.
4. Place Chinese `.mp4` videos in `Pending` folder.

### 4. Running Locally

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Set your variables in .env
# Make sure ENABLE_TRANSLATION=true for English output

# Run the scheduler
python src/scheduler.py
```

### 5. Running via GitHub Actions

Push to GitHub, set Repository Secrets, and the workflow runs every 4 hours automatically.

### 6. How Translation Works

```
Chinese Video (Google Drive)
    ↓
Step 1: Extract Audio (ffmpeg)
    ↓
Step 2: Transcribe Chinese → Text (OpenAI Whisper)
    ↓
Step 3: Translate Chinese → English (OpenAI GPT)
    ↓
Step 4: Generate English Audio (edge-tts)
    ↓
Step 5: Merge English Audio + Original Video
    ↓
Step 6: Add Dual Subtitles (Chinese + English)
    ↓
English Dubbed Video → Upload to Facebook & YouTube
```

### 7. Configuration Options

```bash
# Translation settings in .env
ENABLE_TRANSLATION=true          # Enable/disable translation
TTS_VOICE=en-US-ChristopherNeural  # English voice
SUBTITLE_LANGUAGE=dual           # english, chinese, or dual

# Content settings
CHINESE_CONTENT_SOURCE=douyin    # weibo, douyin, bilibili, kuaishou
CHINESE_CONTENT_CATEGORY=culture # music, food, travel, comedy, culture
CHINESE_TARGET_REGION=united_states
```

## 📁 Project Structure

```
Facebook-Viral-Chinese-Reels/
├── src/
│   ├── scheduler.py          # US Eastern Time scheduling
│   ├── queue_manager.py      # Core workflow with translation
│   ├── translator.py         # Chinese → English pipeline
│   ├── seo_generator.py      # US audience SEO
│   ├── facebook_uploader.py  # Facebook Graph API
│   ├── youtube_uploader.py   # YouTube Shorts upload
│   ├── agent_2_editor.py     # NotoSansSC font, 热门 label
│   ├── agent_3_uploader.py   # English hashtags
│   ├── agent_4_reporter.py   # English Telegram reports
│   └── ... (17 files total)
├── .github/workflows/        # GitHub Actions CI/CD
├── .env.example              # US audience config
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 📊 Logging

Logs are saved to `logs/agent.log` with timestamps and levels (INFO, WARNING, ERROR).

## 📄 License

MIT License - See `privacy-policy.html` for details.
