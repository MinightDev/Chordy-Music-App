import os
import tkinter as tk
from tkinter import ttk, messagebox
from pytube import YouTube
import pygame
from pytube.cli import on_progress
from pytube.exceptions import RegexMatchError
import yt_dlp
from datetime import timedelta
from mutagen.mp3 import MP3
import subprocess
import webbrowser


class MusicPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ZBotify v1.0")
        self.load_author()

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", foreground="#f56464", font=("Helvetica", 12))
        self.label = ttk.Label(root, text="Enter a song keyword:", font=("Helvetica", 14, "bold"))
        self.label.pack(pady=10)

        self.entry = ttk.Entry(root, font=("Helvetica", 12))
        self.entry.pack(pady=5)
        self.placeholder_text = "Enter a song name.."
        self.entry.insert(0, self.placeholder_text)

        self.entry.bind("<FocusIn>", self.remove_placeholder)
        self.entry.bind("<FocusOut>", self.restore_placeholder)

        self.search_button = ttk.Button(root, text="Search and Play", command=self.search_and_play)
        self.search_button.pack(pady=5)

        self.play_button = ttk.Button(root, text="Play", command=self.play_music, state=tk.DISABLED)
        self.play_button.pack(pady=5)

        self.pause_button = ttk.Button(root, text="Stop", command=self.pause_music, state=tk.DISABLED)
        self.pause_button.pack(pady=5)

        self.prev_button = ttk.Button(root, text="Previous", command=self.play_previous, state=tk.DISABLED)
        self.prev_button.pack(pady=5)

        self.next_button = ttk.Button(root, text="Next", command=self.play_next, state=tk.DISABLED)
        self.next_button.pack(pady=5)

        self.quit_button = ttk.Button(root, text="Quit", command=self.quit_app)
        self.quit_button.pack(pady=10)

        self.volume_scale = ttk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, command=self.adjust_volume)
        self.volume_scale.set(50) # initialized the volume to 50
        self.volume_scale.pack(pady=5)

        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        self.song_files = []
        self.played_songs = []
        self.current_song_index = -1
        self.current_song_length = 0
        self.playback_progress = 0

        self.label = ttk.Label(root, text=f"Please consider leaving a ⭐ to support the continuation of this project.\n", font=("Helvetica", 9, "bold"))
        self.label.pack(pady=5)
        self.author_label = tk.Label(root, text=f"By {self.author}", font=("Helvetica", 10, "bold"), cursor="hand2")
        self.author_label.pack(pady=5)
        self.author_label.bind("<Button-1>", self.open_author_website)

        if not os.path.exists("mzika"):
            os.mkdir("mzika")

        pygame.mixer.init()

        self.playback_timer = self.root.after(100, self.update_playback_progress)



    def open_author_website(self, event):
        webbrowser.open("https://github.com/MinightDev/ZBotify-Music-Streaming-App")

    def remove_placeholder(self, event):
        if self.entry.get() == self.placeholder_text:
            self.entry.delete(0, tk.END)

    def restore_placeholder(self, event):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder_text)

    def load_author(self):
        try:
            import json
            with open("bin/config.json", "r") as config_file:
                config = json.load(config_file)
                self.author = config.get("author", "Minight")
        except Exception:
            self.author = "Minight"

    def search_and_play(self):
        song_keyword = self.entry.get()
        try:
            video_url = self.search_video(song_keyword)

            # Download the audio in webm format
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join("mzika", "%(id)s.%(ext)s"),
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                song_id = info['id']
                webm_file = os.path.join("mzika", f"{song_id}.webm")

            # Convert webm to mp3 using ffmpeg
            mp3_file = os.path.join("mzika", f"{song_id}.mp3")
            ffmpeg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin", "ffmpeg")
            convert_command = [ffmpeg_path, "-i", webm_file, "-b:a", "320k", mp3_file]
            subprocess.run(convert_command)

            os.remove(webm_file)

            # Play the downloaded song
            self.song_files.append(mp3_file)
            self.current_song_index = len(self.song_files) - 1  # Set the index to the new song
            self.play_selected_song()  # Play the newly downloaded song

            self.play_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.NORMAL)
            self.prev_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)
            
            self.playback_progress = 0
            self.current_song_length = self.get_audio_length(mp3_file)
            self.playback_timer = self.root.after(100, self.update_playback_progress)
            self.playback_counter.set(self.format_time(self.current_song_length))
        except RegexMatchError:
            messagebox.showerror("Error", "No matching music found.")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def get_audio_length(self, audio_file):
        try:
            audio = MP3(audio_file)
            return int(audio.info.length * 1000)
        except Exception:
            return 0

    def adjust_volume(self, volume):
        volume_level = float(volume) / 100
        pygame.mixer.music.set_volume(volume_level)

    def search_video(self, keyword):
        ydl_opts = {
            'default_search': 'ytsearch',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'ytsearch:{keyword}', download=False)
            if 'entries' in info:
                return info['entries'][0]['webpage_url']
        raise RegexMatchError('No matching video found.')

    def play_music(self):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.unpause()
            else:
                self.play_selected_song()

            self.play_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.prev_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def pause_music(self):
        try:
            pygame.mixer.music.pause()
            self.play_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def play_selected_song(self):
        try:
            if self.current_song_index >= 0:
                self.play_song(self.song_files[self.current_song_index])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def play_previous(self):
        if self.current_song_index > 0:
            self.current_song_index -= 1
            self.play_song(self.song_files[self.current_song_index])

    def play_next(self):
        if self.current_song_index < len(self.song_files) - 1:
            self.current_song_index += 1
            self.play_song(self.song_files[self.current_song_index])

    def play_song(self, song_file):
        try:
            pygame.mixer.music.load(song_file)
            pygame.mixer.music.play()

            self.current_song_length = self.get_audio_length(song_file)
            self.playback_progress = 0
            self.playback_timer = self.root.after(100, self.update_playback_progress)
            self.playback_counter.set(self.format_time(self.current_song_length))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_playback_progress(self):
        if pygame.mixer.music.get_busy():
            self.playback_progress += 100
            if self.playback_progress > self.current_song_length:
                self.playback_progress = self.current_song_length
            self.progress_bar['value'] = (self.playback_progress / self.current_song_length) * 100
            self.playback_counter.set(self.format_time(self.current_song_length - self.playback_progress))
            self.root.after(100, self.update_playback_progress)
        else:
            self.progress_bar['value'] = self.playback_progress

    def format_time(self, milliseconds):
        total_seconds = milliseconds // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02}"

    def quit_app(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        pygame.mixer.quit()

        if self.song_files:
            for song_file in self.song_files:
                if os.path.exists(song_file):
                    os.remove(song_file)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayerApp(root)
    root.iconbitmap("icon.ico")

    app.progress_bar = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate', style="Custom.Horizontal.TProgressbar")
    app.progress_bar.pack(pady=10)

    style = ttk.Style()
    style.configure("Custom.Horizontal.TProgressbar", foreground="green")

    app.playback_counter = tk.StringVar()
    playback_label = ttk.Label(root, textvariable=app.playback_counter)
    playback_label.pack()

    root.mainloop()