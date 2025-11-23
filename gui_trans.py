import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from youtube_transcript_api import YouTubeTranscriptApi
import os
import re
from urllib.parse import parse_qs, urlparse
from pytube import Playlist, YouTube
import threading
import time

class TranscriptDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Transcript Downloader")
        self.root.geometry("800x600")
        
        self.video_list = []
        self.is_downloading = False
        
        # URL Input Frame
        url_frame = ttk.LabelFrame(root, text="Enter URL", padding=10)
        url_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(url_frame, text="YouTube URL:").grid(row=0, column=0, sticky="w", pady=5)
        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.load_btn = ttk.Button(url_frame, text="Load", command=self.load_url)
        self.load_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Playlist Options Frame
        self.playlist_frame = ttk.LabelFrame(root, text="Playlist Options", padding=10)
        self.playlist_frame.pack(fill="x", padx=10, pady=5)
        self.playlist_frame.pack_forget()  # Hide initially
        
        ttk.Label(self.playlist_frame, text="Start from video:").grid(row=0, column=0, sticky="w", pady=5)
        self.start_video_var = tk.StringVar(value="1")
        self.start_video_combo = ttk.Combobox(self.playlist_frame, textvariable=self.start_video_var, 
                                               state="readonly", width=50)
        self.start_video_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.playlist_frame.columnconfigure(1, weight=1)
        
        # Video List Frame
        list_frame = ttk.LabelFrame(root, text="Videos to Download", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.video_listbox = tk.Listbox(list_frame, height=10)
        self.video_listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.video_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.video_listbox.config(yscrollcommand=scrollbar.set)
        
        # Output Folder Frame
        folder_frame = ttk.LabelFrame(root, text="Output Folder", padding=10)
        folder_frame.pack(fill="x", padx=10, pady=5)
        
        self.folder_var = tk.StringVar(value="transcripts")
        ttk.Entry(folder_frame, textvariable=self.folder_var, width=50).pack(side="left", padx=5)
        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side="left", padx=5)
        
        # Download Button
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.download_btn = ttk.Button(btn_frame, text="Start Download", command=self.start_download)
        self.download_btn.pack(side="left", padx=5)
        
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.cancel_download, state="disabled")
        self.cancel_btn.pack(side="left", padx=5)
        
        # Progress Frame
        progress_frame = ttk.LabelFrame(root, text="Progress", padding=10)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(anchor="w")
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill="x", pady=5)
        
        # Log Frame
        log_frame = ttk.LabelFrame(root, text="Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state="disabled")
        self.log_text.pack(fill="both", expand=True)
    
    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
    
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)
    
    def is_playlist(self, url):
        return 'list=' in url
    
    def extract_video_id(self, url):
        if 'watch?v=' in url:
            return url.split('watch?v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            return url.split('youtu.be/')[1].split('?')[0]
        return None
    
    def load_url(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        self.log("Loading URL...")
        self.load_btn.config(state="disabled")
        
        # Run in thread to avoid freezing UI
        thread = threading.Thread(target=self._load_url_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def _load_url_thread(self, url):
        try:
            if self.is_playlist(url):
                self.log("Detected playlist URL")
                playlist = Playlist(url)
                
                self.video_list = []
                total = len(playlist.video_urls)
                for idx, video_url in enumerate(playlist.video_urls, 1):
                    self.root.after(0, lambda i=idx, t=total: self.log(f"Loading video {i}/{t}..."))
                    video_id = self.extract_video_id(video_url)
                    if video_id:
                        try:
                            yt = YouTube(video_url)
                            title = yt.title
                        except Exception as e:
                            self.root.after(0, lambda e=e: self.log(f"  Warning: Could not fetch title - {e}"))
                            title = video_id
                        self.video_list.append({'id': video_id, 'title': title, 'url': video_url})
                
                self.root.after(0, self._update_playlist_ui)
            else:
                self.log("Detected single video URL")
                video_id = self.extract_video_id(url)
                if video_id:
                    try:
                        yt = YouTube(url)
                        title = yt.title
                    except Exception as e:
                        self.root.after(0, lambda e=e: self.log(f"Warning: Could not fetch title - {e}"))
                        title = video_id
                    self.video_list = [{'id': video_id, 'title': title, 'url': url}]
                    self.root.after(0, self._update_single_video_ui)
                else:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Invalid YouTube URL"))
                    self.root.after(0, lambda: self.load_btn.config(state="normal"))
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Error loading URL: {e}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load URL: {e}"))
            self.root.after(0, lambda: self.load_btn.config(state="normal"))
    
    def _update_playlist_ui(self):
        self.log(f"Found {len(self.video_list)} videos in playlist")
        
        # Show playlist frame
        self.playlist_frame.pack(fill="x", padx=10, pady=5, after=self.url_entry.master)
        
        # Update dropdown
        options = [f"{i+1}. {v['title']}" for i, v in enumerate(self.video_list)]
        self.start_video_combo['values'] = options
        self.start_video_combo.current(0)
        self.start_video_combo.bind('<<ComboboxSelected>>', self.update_video_list)
        
        # Update video list
        self.update_video_list()
        self.load_btn.config(state="normal")
    
    def _update_single_video_ui(self):
        self.log(f"Loaded video: {self.video_list[0]['title']}")
        
        # Hide playlist frame
        self.playlist_frame.pack_forget()
        
        # Update video list
        self.video_listbox.delete(0, tk.END)
        self.video_listbox.insert(tk.END, f"1. {self.video_list[0]['title']}")
        
        self.load_btn.config(state="normal")
    
    def update_video_list(self, event=None):
        start_index = self.start_video_combo.current()
        
        self.video_listbox.delete(0, tk.END)
        for i in range(start_index, len(self.video_list)):
            self.video_listbox.insert(tk.END, f"{i+1}. {self.video_list[i]['title']}")
    
    def start_download(self):
        if not self.video_list:
            messagebox.showerror("Error", "Please load a URL first")
            return
        
        output_folder = self.folder_var.get()
        if not output_folder:
            messagebox.showerror("Error", "Please specify an output folder")
            return
        
        # Create output folder
        os.makedirs(output_folder, exist_ok=True)
        
        # Determine start index
        if self.playlist_frame.winfo_ismapped():
            start_index = self.start_video_combo.current()
        else:
            start_index = 0
        
        self.is_downloading = True
        self.download_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.load_btn.config(state="disabled")
        
        # Start download in thread
        thread = threading.Thread(target=self._download_thread, args=(start_index, output_folder))
        thread.daemon = True
        thread.start()
    
    def _download_thread(self, start_index, output_folder):
        api = YouTubeTranscriptApi()
        total_videos = len(self.video_list) - start_index
        success_count = 0
        error_count = 0
        
        self.root.after(0, lambda: self.progress_bar.config(maximum=total_videos, value=0))
        
        for i in range(start_index, len(self.video_list)):
            if not self.is_downloading:
                self.root.after(0, lambda: self.log("Download cancelled"))
                break
            
            video = self.video_list[i]
            video_num = i + 1
            
            self.root.after(0, lambda v=video_num, t=total_videos: 
                           self.progress_var.set(f"Processing video {v}/{len(self.video_list)}"))
            self.root.after(0, lambda: self.log(f"\n[{video_num}/{len(self.video_list)}] Processing: {video['title']}"))
            
            try:
                # Fetch transcript
                time.sleep(1)  # Rate limiting
                transcript_result = api.fetch(video['id'])
                
                # Extract text
                full_text = " ".join([snippet.text for snippet in transcript_result.snippets])
                
                # Create filename
                safe_title = re.sub(r'[<>:"/\\|?*]', '', video['title'])
                filename = f"{video_num:02d}_{safe_title}.txt"
                filepath = os.path.join(output_folder, filename)
                
                # Save to file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Video ID: {video['id']}\n")
                    f.write(f"Title: {video['title']}\n")
                    f.write(f"URL: {video['url']}\n")
                    f.write(f"Language: {transcript_result.language} ({transcript_result.language_code})\n")
                    f.write("-" * 80 + "\n\n")
                    f.write(full_text)
                
                success_count += 1
                self.root.after(0, lambda f=filepath: self.log(f"✓ Saved to: {f}"))
                
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                self.root.after(0, lambda e=error_msg: self.log(f"✗ Error: {e}"))
                
                if "IpBlocked" in error_msg or "blocked" in error_msg.lower():
                    self.root.after(0, lambda: self.log("\n⚠ YouTube is blocking requests. Stopping download."))
                    break
            
            self.root.after(0, lambda v=i-start_index+1: self.progress_bar.config(value=v))
        
        # Complete
        self.root.after(0, lambda: self.progress_var.set(
            f"Completed! {success_count} successful, {error_count} failed"))
        self.root.after(0, lambda: self.log(f"\n{'='*60}"))
        self.root.after(0, lambda: self.log(f"Download completed: {success_count} successful, {error_count} failed"))
        self.root.after(0, lambda: self.log(f"Transcripts saved in '{output_folder}'"))
        self.root.after(0, lambda: self.log(f"{'='*60}"))
        
        self.root.after(0, self._reset_buttons)
    
    def cancel_download(self):
        self.is_downloading = False
        self.cancel_btn.config(state="disabled")
    
    def _reset_buttons(self):
        self.download_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        self.load_btn.config(state="normal")
        self.is_downloading = False

if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptDownloaderGUI(root)
    root.mainloop()
