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
from pypresence import Presence
import pypresence
import time


class MusicPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chordy v1.0")
        self.load_author()
        self.rpc = Presence("1146241395267481633")
        self.rpc.connect()

        pygame.mixer.init()
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", foreground="#2A9D8F", font=("Helvetica", 12))

        self.label = ttk.Label(root, text="Chordy Music", font=("Helvetica", 17, "bold"), foreground="#2A9D8F")
        self.label.pack(pady=10)

        self.entry = ttk.Entry(root, font=("Helvetica", 14), width=20, foreground="gray")
        self.entry.pack(pady=5)
        self.placeholder_text = "Enter a song name.."
        self.entry.insert(0, self.placeholder_text)

        self.entry.bind("<FocusIn>", self.remove_placeholder)
        self.entry.bind("<FocusOut>", self.restore_placeholder)

        self.search_button = ttk.Button(root, text="Search and Play", cursor="hand2", command=self.search_and_play)
        self.search_button.pack(pady=5)

        self.play_button = ttk.Button(root, text="Play", cursor="hand2", command=self.play_music, state=tk.DISABLED)
        self.play_button.pack(pady=5)

        self.pause_button = ttk.Button(root, text="Stop", cursor="hand2", command=self.pause_music, state=tk.DISABLED)
        self.pause_button.pack(pady=5)

        self.prev_button = ttk.Button(root, text="Previous", cursor="hand2", command=self.play_previous, state=tk.DISABLED)
        self.prev_button.pack(pady=5)

        self.next_button = ttk.Button(root, text="Next", cursor="hand2", command=self.play_next, state=tk.DISABLED)
        self.next_button.pack(pady=5)

        self.quit_button = ttk.Button(root, text="Loop", cursor="hand2", command=self.quit_app)
        self.quit_button.pack(pady=10)

        self.volume_label = ttk.Label(root, text="Volume:")
        self.volume_label.pack(pady=5)

        self.volume_scale = ttk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, command=self.adjust_volume)
        self.volume_scale.set(50)
        self.volume_scale.pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        self.song_files = []
        self.played_songs = []
        self.current_song_index = -1
        self.current_song_length = 0
        self.playback_progress = 0

        self.author_label = tk.Label(root, text=f"Author: {self.author}", font=("Helvetica", 10, "bold"), cursor="hand2")
        self.author_label.pack(pady=5)
        self.author_label.bind("<Button-1>", self.open_author_website)

        if not os.path.exists("mzika"):
            os.mkdir("mzika")

        pygame.mixer.init()

        self.playback_timer = self.root.after(100, self.update_playback_progress)


    def update_discord_rich_presence(self):
        if self.current_song_index >= 0:
            song_name = os.path.basename(self.song_files[self.current_song_index])
            self.rpc.update(
                details="Listening to music",
                state=f"Playing: {song_name}",
                large_image="qfzajzm",
                small_image="green-circle-icon-28",
                large_text="Chordy",
                small_text="Download me now!!!",
                start=int(time.time()) - self.playback_progress // 1000,
                end=int(time.time()) + (self.current_song_length - self.playback_progress) // 1000,
                buttons=[
                    {"label": "Download", "url": "https://github.com/MinightDev/ZBotify-Music-Streaming-App"}
                ]
            )

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

            self.song_files.append(mp3_file)
            self.current_song_index = len(self.song_files) - 1
            self.play_selected_song()

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

            self.update_discord_rich_presence()

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

            pygame.mixer.music.set_endevent(pygame.USEREVENT)

            self.update_discord_rich_presence()

            self.play_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.prev_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("Error", str(e))


    def update_playback_progress(self):
        if pygame.mixer.music.get_busy():
            current_time = pygame.mixer.music.get_pos()
            self.progress_bar['value'] = (current_time / self.current_song_length) * 100
            self.playback_counter.set(self.format_time(self.current_song_length - current_time))
            self.root.after(100, self.update_playback_progress)
        else:
            self.progress_bar['value'] = 0 
            
            self.play_next()

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

        mzika_directory = "mzika"
        for filename in os.listdir(mzika_directory):
            file_path = os.path.join(mzika_directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayerApp(root)
    root.iconbitmap("icon.ico")

    app.progress_bar = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=300, mode='determinate', style="Custom.Horizontal.TProgressbar")
    app.progress_bar.pack(pady=10)

    style = ttk.Style()
    style.configure("Custom.Horizontal.TProgressbar", foreground="green", background="#2A9D8F")

    app.playback_counter = tk.StringVar()
    playback_label = ttk.Label(root, textvariable=app.playback_counter, font=("Helvetica", 10))
    playback_label.pack()

    app.like_button = ttk.Button(root, text="❤")
    app.like_button.pack(side=tk.LEFT, padx=10)
    app.quit_button = ttk.Button(root, text="❌", command=app.quit_app)
    app.quit_button.pack(side=tk.RIGHT, padx=10)

    root.mainloop()