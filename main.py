"""
YouTube Transcript Downloader
Main entry point - launches the web interface
"""
import os
import webbrowser
import time
import threading
from web_trans import app

def open_browser():
    """Open browser after a short delay to allow server to start"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("=" * 60)
    print("YouTube Transcript Downloader")
    print("=" * 60)
    print("\nStarting web server...")
    print("Opening browser at http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    # Open browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Flask server
    app.run(debug=False, port=5000)
