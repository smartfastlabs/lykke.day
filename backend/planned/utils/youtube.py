import os
import signal
import subprocess

# Track the current player process
player_process: subprocess.Popen | None = None


def kill_current_player():
    """Stop any currently playing audio."""
    global player_process
    if player_process and player_process.poll() is None:
        os.killpg(os.getpgid(player_process.pid), signal.SIGTERM)
        player_process = None


def play_audio(url: str):
    """Play audio from a YouTube URL using yt-dlp and mpv."""
    global player_process

    kill_current_player()

    # yt-dlp extracts the audio URL, mpv plays it
    # --no-video ensures audio-only playback
    player_process = subprocess.Popen(
        [
            "mpv",
            "--no-video",
            "--ytdl-format=bestaudio",
            url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # Allows it to run independently
    )
