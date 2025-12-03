"""Test script for download functionality"""
import sys
import os
sys.path.insert(0, '.')
import downloader

# Setup
UPLOAD_FOLDER = 'downloads_bot'
FFMPEG_FOLDER = 'ffmpeg_local'
downloader.setup(UPLOAD_FOLDER, FFMPEG_FOLDER)

print("="*60)
print("TEST: Download YouTube Video")
print("="*60)

url = "https://www.youtube.com/watch?v=ST23wVrz5_w"
output_path = os.path.join(UPLOAD_FOLDER, "test_download.mp3")

try:
    print(f"\nURL: {url}")
    print(f"Output: {output_path}")
    print("\nStarting download...")
    
    final_path, final_filename = downloader.download_youtube(url, output_path)
    
    print(f"\n✓ Download successful!")
    print(f"  File path: {final_path}")
    print(f"  Filename: {final_filename}")
    
    # Check file exists
    if os.path.exists(final_path):
        file_size = os.path.getsize(final_path)
        print(f"  File size: {file_size / (1024*1024):.2f} MB")
        print(f"\n✓ File exists and is ready to send!")
        
        # Cleanup
        print(f"\nCleaning up test file...")
        os.remove(final_path)
        print("✓ Cleanup complete")
    else:
        print(f"\n✗ ERROR: File not found at {final_path}")
        
except Exception as e:
    print(f"\n✗ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Test complete!")
print("="*60)
