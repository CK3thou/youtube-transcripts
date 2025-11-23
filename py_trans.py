from youtube_transcript_api import YouTubeTranscriptApi
import os
import re
from urllib.parse import parse_qs, urlparse
import requests
from pytube import Playlist
import time

def get_playlist_video_ids(playlist_url):
    """Extract all video IDs from a YouTube playlist URL"""
    try:
        playlist = Playlist(playlist_url)
        video_ids = []
        
        # Get video URLs and extract IDs
        for url in playlist.video_urls:
            # Extract video ID from URL
            if 'watch?v=' in url:
                video_id = url.split('watch?v=')[1].split('&')[0]
                video_ids.append(video_id)
        
        return video_ids
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return []

def sanitize_filename(title):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '', title)

def get_video_title(video_id):
    """Try to get video title from YouTube"""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            # Try multiple patterns to extract title
            patterns = [
                r'"title":"([^"]+)"',
                r'<title>([^<]+)</title>',
                r'property="og:title" content="([^"]+)"'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    title = match.group(1)
                    # Clean up the title
                    title = title.replace(' - YouTube', '')
                    # Decode HTML entities
                    title = title.encode().decode('unicode_escape')
                    return title
    except Exception as e:
        print(f"  Warning: Could not fetch title: {e}")
    
    return video_id

playlist_url = 'https://www.youtube.com/watch?v=gwZIgkyOPns&list=PLOR30RPQx4ZqxioCWsp68zM_zSaFMT4kM&index=6'
output_folder = 'transcripts'

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

try:
    print("Fetching playlist videos...")
    video_ids = get_playlist_video_ids(playlist_url)
    print(f"Found {len(video_ids)} videos in playlist\n")
    
    if not video_ids:
        print("No videos found in playlist. Please check the URL.")
        exit(1)
    
    # Initialize the API
    api = YouTubeTranscriptApi()
    
    success_count = 0
    error_count = 0
    start_from = 12  # Start from video 12
    
    for idx, video_id in enumerate(video_ids, 1):
        # Skip videos before the starting index
        if idx < start_from:
            continue
            
        try:
            print(f"[{idx}/{len(video_ids)}] Processing video: {video_id}")
            
            # Get video title
            video_title = get_video_title(video_id)
            print(f"  Title: {video_title}")
            
            # Fetch the transcript with rate limiting
            time.sleep(5)  # Add delay to avoid IP blocking
            
            transcript_result = api.fetch(video_id)
            
            # Extract text from snippets
            full_text = ""
            for snippet in transcript_result.snippets:
                full_text += snippet.text + " "
            
            # Create filename
            safe_title = sanitize_filename(video_title)
            filename = f"{idx:02d}_{safe_title}.txt"
            filepath = os.path.join(output_folder, filename)
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Video ID: {video_id}\n")
                f.write(f"Title: {video_title}\n")
                f.write(f"URL: https://www.youtube.com/watch?v={video_id}\n")
                f.write(f"Language: {transcript_result.language} ({transcript_result.language_code})\n")
                f.write("-" * 80 + "\n\n")
                f.write(full_text)
            
            print(f"  ✓ Saved to: {filepath}\n")
            success_count += 1
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ✗ Error: {error_msg}\n")
            error_count += 1
            
            # If IP blocked, stop processing
            if "IpBlocked" in error_msg or "blocked" in error_msg.lower():
                print("\n⚠ YouTube is blocking requests from your IP.")
                print("This happened because too many requests were made.")
                print("Please wait a while before trying again, or use a VPN/proxy.")
                break
            
            continue
    
    print(f"\n{'='*60}")
    print(f"Completed! {success_count} successful, {error_count} failed")
    print(f"Transcripts saved in '{output_folder}' folder")
    print(f"{'='*60}")

except Exception as e:
    print(f"Fatal error: {e}")