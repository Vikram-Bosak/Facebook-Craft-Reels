import os
import sys

# Load env variables from .env
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from agent_4_reporter import send_discord_webhook

def main():
    message = (
        "🚀 **Facebook-Craft-Reels Final Production Report** 🚀\n\n"
        "🟢 **Project Status**: Production Ready & Pushed to GitHub\n"
        "🔗 **GitHub Repo**: [Facebook-Craft-Reels](https://github.com/Vikram-Bosak/Facebook-Craft-Reels)\n\n"
        
        "🛠️ **Key Features & Audio Improvements implemented:**\n"
        "• **Original Sound Effects Preserved**: Successfully isolated original SFX using standard Demucs 4-stem separation (without vocal bleed). Mixed at **90% volume** for premium auditory experience.\n"
        "• **Dubbed English Voice Volume**: Tuned English voice volume to **60%** (from 100%) to ensure original SFX are clearly audible.\n"
        "• **Slower Voice Speeds**: Configured natural speech rate (Edge-TTS: `-20%`, Kokoro/OpenAI: `0.9` speed).\n"
        "• **Uniform Lofi BGM**: Applied the same high-quality Lofi track (`cute-lofi.mp3`, looped) across all reels, set at a subtle **8% volume**.\n\n"
        
        "✅ **Dependencies & Infrastructure Fixed:**\n"
        "• **Torchaudio Patch**: Patched virtual environment's `torchaudio.save` to use the standard `soundfile` backend. This bypassed the broken `torchcodec` dependency on Windows, allowing Demucs to execute successfully.\n\n"
        
        "🤖 **Telegram Agent Controller Online:**\n"
        "• Configured in **Agent-Routing mode** (`use_nvidia_api: false`).\n"
        "• Locked to active conversation ID (`0c27bde1-d00e-44bd-8bad-1e1616eedcec`).\n"
        "• Actively running in background as a persistent service.\n\n"
        
        "🎬 **Processed Videos (Delivered to Phone):**\n"
        "1. *Origami Minecraft Creeper* (BV17u411L7nP)\n"
        "2. *DIY Paper Cat Toy* (BV1J2TE6uEpA)\n"
        "3. *DIY Shaking Paper Craft Toy* (BV1E6EX6hEks) *(With final 90%/60%/8% audio mix)*"
    )
    
    print("Sending final production report to Discord webhook...")
    success = send_discord_webhook(message)
    if success:
        print("Report sent successfully!")
        sys.exit(0)
    else:
        print("Failed to send report.")
        sys.exit(1)

if __name__ == "__main__":
    main()
