import os
import subprocess
from pathlib import Path

def create_dummy_mp4(filename, duration=10, output_dir=None):
    """Create a valid dummy MP4 file with specified name and duration."""
    try:
        # Use current directory if no output_dir specified
        output_dir = output_dir or os.getcwd()
        output_dir = Path(output_dir)
        
        # Ensure output directory exists
        if not output_dir.exists():
            print(f"Error: Directory {output_dir} does not exist")
            return None
            
        # Create full file path
        filepath = output_dir / filename
        
        # Get ffmpeg path from environment or use relative to script
        ffmpeg_path = os.getenv('FFMPEG_PATH') or r"C:\Users\ericj\Downloads\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
        ffmpeg_path = Path(ffmpeg_path)
        
        if not ffmpeg_path.exists():
            print(f"Error: FFmpeg not found at {ffmpeg_path}")
            return None
        
        # FFmpeg command to create a valid MP4 file with color bars
        ffmpeg_cmd = [
            str(ffmpeg_path),  # Convert Path to string for subprocess
            '-f', 'lavfi',
            '-i', f'color=c=black:s=1280x720:d={duration}',
            '-c:v', 'libx264',
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            str(filepath)  # Convert Path to string for subprocess
        ]
        
        # Run FFmpeg
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Created valid MP4 file: {filename}")
            print(f"Location: {filepath}")
            print(f"Duration: {duration} seconds")
            return str(filepath)
        else:
            print(f"Error creating MP4: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"Error creating dummy file: {str(e)}")
        return None

def create_test_files(output_dir=None):
    """Create multiple test files with different names."""
    test_files = [
        "The Shawshank Redemption (1994).mp4",
        "Pulp Fiction (1994).mp4",
        "The Good, the Bad and the Ugly (1966).mp4",
        "12 Angry Men (1957).mp4",
        "Schindler's List (1993).mp4"
    ]
    
    created_files = []
    for filename in test_files:
        path = create_dummy_mp4(filename, duration=5, output_dir=output_dir)  # 5-second videos
        if path:
            created_files.append(path)
    
    print(f"\nCreated {len(created_files)} test files")
    return created_files

if __name__ == "__main__":
    print("Creating test files...")
    create_test_files()
    input("Press Enter to exit...")