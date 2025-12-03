"""Test script for music recognition functionality"""
import sys
import os
import asyncio
sys.path.insert(0, '.')
import downloader

# Setup
UPLOAD_FOLDER = 'downloads_bot'
FFMPEG_FOLDER = 'ffmpeg_local'
downloader.setup(UPLOAD_FOLDER, FFMPEG_FOLDER)

async def test_recognition():
    print("="*60)
    print("TEST: Music Recognition with Shazam")
    print("="*60)
    
    # Test URL - using a popular song
    url = "https://www.youtube.com/watch?v=ST23wVrz5_w"
    
    # Test with different timecode formats
    timecode_str = "30;1.00;1h"
    timecode_parts = timecode_str.split(';')
    
    print(f"\nURL: {url}")
    print(f"Timecodes to test: {timecode_str}")
    
    try:
        # Parse timecodes
        print("\n--- Parsing Timecodes ---")
        timecodes = []
        for tc in timecode_parts:
            parsed = downloader.parse_timecode(tc.strip())
            timecodes.append(parsed)
            print(f"  '{tc}' -> {parsed}s")
        
        print(f"\n--- Starting Music Recognition ---")
        print("Note: This will download audio and analyze with Shazam")
        print("This may take a few minutes...\n")
        
        result = await downloader.recognize_music_from_url(url, timecodes)
        
        if result['found']:
            print("\n✓ Music Identified!")
            print(f"  Title: {result['title']}")
            print(f"  Artist: {result['artist']}")
            print(f"  Found at: {result['timecode']}s")
            
            if result.get('cover_art'):
                print(f"  Cover art: {result['cover_art']}")
            
            if 'links' in result and result['links']:
                print("\n  Links found:")
                for platform, link in result['links'].items():
                    print(f"    {platform}: {link}")
        else:
            print(f"\n✗ Music not recognized")
            print(f"  Message: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)

# Run the async test
if __name__ == "__main__":
    asyncio.run(test_recognition())
