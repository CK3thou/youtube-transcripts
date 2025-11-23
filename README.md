# YouTube Transcript Downloader

A Python application to download transcripts from YouTube videos and playlists with both web and desktop interfaces.

## Features

- 🎬 Download transcripts from individual YouTube videos or entire playlists
- 🌐 Modern web interface accessible from any browser
- 🖥️ Desktop GUI application (tkinter)
- 📝 Command-line interface for automation
- 📦 Export transcripts as individual text files or ZIP archive
- 🎯 Select which video to start downloading from in playlists
- 📊 Real-time progress tracking and detailed logs
- 🎨 Beautiful, responsive design

## Installation

1. Clone the repository:
```bash
git clone https://github.com/justthatuser/youtube-transcripts.git
cd youtube-transcripts
```

2. Install dependencies:
```bash
pip install youtube-transcript-api pytube requests beautifulsoup4 flask flask-cors
```

## Usage

### Quick Start (Recommended)

Simply run the main application:
```bash
python main.py
```

This will automatically start the web server and open your browser to the interface.

### Web Interface

1. Start the web server:
```bash
python web_trans.py
```

2. Open your browser and go to: `http://localhost:5000`

3. Paste a YouTube video or playlist URL and click "Load"

4. Select starting video (for playlists) and click "Start Download"

5. Download transcripts as ZIP file when complete

### Desktop GUI

```bash
python gui_trans.py
```

### Command Line

Edit `py_trans.py` to set your playlist URL and run:
```bash
python py_trans.py
```

## Requirements

- Python 3.7+
- youtube-transcript-api
- pytube
- requests
- beautifulsoup4
- flask (for web interface)
- flask-cors (for web interface)
- tkinter (usually comes with Python, for desktop GUI)

## Output Format

Each transcript is saved as a text file with:
- Video ID
- Video title
- Video URL
- Language and language code
- Full transcript text

Files are named: `##_VideoTitle.txt`

## Notes

- Rate limiting is implemented (1 second delay between videos) to avoid IP blocking
- If YouTube blocks your IP, wait 15-30 minutes or use a VPN
- Transcripts are only available for videos that have captions enabled

## License

MIT License

## Author

Created by justthatuser
