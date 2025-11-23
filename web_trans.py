from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import Playlist, YouTube
import os
import re
import time
import zipfile
from io import BytesIO

app = Flask(__name__)
CORS(app)

def extract_video_id(url):
    if 'watch?v=' in url:
        return url.split('watch?v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    return None

def is_playlist(url):
    return 'list=' in url

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/load_url', methods=['POST'])
def load_url():
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        video_list = []
        
        if is_playlist(url):
            playlist = Playlist(url)
            for idx, video_url in enumerate(playlist.video_urls, 1):
                video_id = extract_video_id(video_url)
                if video_id:
                    try:
                        yt = YouTube(video_url)
                        title = yt.title
                    except Exception as e:
                        # Fallback: try to get title from video page
                        try:
                            import requests
                            response = requests.get(video_url)
                            match = re.search(r'<title>([^<]+)</title>', response.text)
                            if match:
                                title = match.group(1).replace(' - YouTube', '').strip()
                            else:
                                title = f"Video {idx}"
                        except:
                            title = f"Video {idx}"
                    
                    video_list.append({
                        'id': video_id,
                        'title': title,
                        'url': video_url
                    })
            
            return jsonify({
                'type': 'playlist',
                'videos': video_list,
                'count': len(video_list)
            })
        else:
            video_id = extract_video_id(url)
            if video_id:
                try:
                    yt = YouTube(url)
                    title = yt.title
                except Exception as e:
                    # Fallback: try to get title from video page
                    try:
                        import requests
                        response = requests.get(url)
                        match = re.search(r'<title>([^<]+)</title>', response.text)
                        if match:
                            title = match.group(1).replace(' - YouTube', '').strip()
                        else:
                            title = video_id
                    except:
                        title = video_id
                
                video_list.append({
                    'id': video_id,
                    'title': title,
                    'url': url
                })
                
                return jsonify({
                    'type': 'video',
                    'videos': video_list,
                    'count': 1
                })
            else:
                return jsonify({'error': 'Invalid YouTube URL'}), 400
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download_transcripts():
    try:
        data = request.json
        videos = data.get('videos', [])
        start_index = data.get('start_index', 0)
        
        if not videos:
            return jsonify({'error': 'No videos provided'}), 400
        
        api = YouTubeTranscriptApi()
        results = []
        
        for i in range(start_index, len(videos)):
            video = videos[i]
            video_num = i + 1
            
            try:
                time.sleep(5)  # Rate limiting to avoid IP blocking
                transcript_result = api.fetch(video['id'])
                
                # Extract text
                full_text = " ".join([snippet.text for snippet in transcript_result.snippets])
                
                # Create filename
                safe_title = re.sub(r'[<>:"/\\|?*]', '', video['title'])
                
                content = f"""Video ID: {video['id']}
Title: {video['title']}
URL: {video['url']}
Language: {transcript_result.language} ({transcript_result.language_code})
{'-'*80}

{full_text}"""
                
                results.append({
                    'success': True,
                    'video_num': video_num,
                    'title': video['title'],
                    'filename': f"{video_num:02d}_{safe_title}.txt",
                    'content': content
                })
                
            except Exception as e:
                error_msg = str(e)
                results.append({
                    'success': False,
                    'video_num': video_num,
                    'title': video['title'],
                    'error': error_msg
                })
                
                # Stop if IP blocked
                if "IpBlocked" in error_msg or "blocked" in error_msg.lower():
                    break
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download_zip', methods=['POST'])
def download_zip():
    try:
        data = request.json
        files = data.get('files', [])
        
        if not files:
            return jsonify({'error': 'No files to download'}), 400
        
        # Create zip file in memory
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_data in files:
                filename = file_data['filename']
                content = file_data['content']
                zf.writestr(filename, content)
        
        memory_file.seek(0)
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='transcripts.zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, port=5000)
