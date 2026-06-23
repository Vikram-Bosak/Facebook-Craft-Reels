import os
import sys
import shutil

# Add src to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from logger import logger
from translator import translate_video

def main():
    # We will use the original downloaded video, which the script will trim to 59s
    raw_video = "workspace/raw_video.mp4"
    if not os.path.exists(raw_video):
        logger.error(f"Trimmed video not found at {raw_video}. Please make sure to run run_pipeline.py first.")
        sys.exit(1)
        
    voices = {
        "Jenny": "en-US-JennyNeural",
        "Guy": "en-US-GuyNeural",
        "Aria": "en-US-AriaNeural"
    }
    
    workspace_dir = "workspace"
    
    for name, voice_id in voices.items():
        logger.info(f"==================================================")
        logger.info(f"Starting translation with voice: {name} ({voice_id})")
        logger.info(f"==================================================")
        
        # Set the voice env variable
        os.environ['TTS_VOICE'] = voice_id
        
        # Run translation pipeline
        output_subdir = os.path.join(workspace_dir, f"out_{name}")
        os.makedirs(output_subdir, exist_ok=True)
        
        result = translate_video(
            raw_video,
            output_dir=output_subdir,
            burn_subtitles=True,
            subtitle_language='dual'
        )
        
        if result and result.get('english_video') and os.path.exists(result['english_video']):
            final_output = f"output_dubbed_{name}.mp4"
            shutil.copy2(result['english_video'], final_output)
            logger.info(f"SUCCESS: Generated video for voice {name} -> {final_output}")
        else:
            logger.error(f"Failed to generate video for voice {name}")

if __name__ == '__main__':
    main()
