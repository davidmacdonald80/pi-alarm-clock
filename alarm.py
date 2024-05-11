#!/home/david/alarm/bin/python

import time
from datetime import datetime, timedelta
from pathlib import Path
from random import choice
from pipewire_python.controller import Controller
import logging
from zoneinfo import ZoneInfo  # For timezone handling including DST

# Setup basic logging
logging.basicConfig(filename='/home/david/alarm/alarm.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Time for the alarm to go off and timezone setting
ALARM_TIME = "06:05"
TIMEZONE = ZoneInfo("America/Chicago")  # Local timezone

def get_next_alarm_time():
    """Calculate the next occurrence of the specified alarm time, considering timezone and DST."""
    alarm_time = datetime.strptime(ALARM_TIME, "%H:%M").time()
    now = datetime.now(TIMEZONE)
    next_alarm = datetime(now.year, now.month, now.day, alarm_time.hour, alarm_time.minute, tzinfo=TIMEZONE)
    if now >= next_alarm:
        next_alarm += timedelta(days=1)
    return next_alarm

def play_song(file_path):
    """Attempt to play a song with error handling for the audio playback."""
    try:
        audio_controller = Controller()
        audio_controller.set_config(rate=48000, channels=2, _format='f64', volume=0.95, quality=11)
        audio_controller.playback(audio_filename=file_path)
        logging.info(f"Successfully played {file_path}")
    except Exception as e:
        logging.error(f"Failed to play {file_path}: {e}")

def play_songs_until_end_time(end_time, songs):
    """Plays random songs until the specified end time."""
    while datetime.now(TIMEZONE) < end_time:
        random_song = choice(songs)
        logging.info(f"Playing song: {random_song}")
        play_song(random_song)
        time.sleep(10)  # Delay between songs, adjust as needed

def main():
    songs = [str(song) for song in Path('/media/audio/got-in-2023/').rglob('*.mp3') if not song.parent.match('@eaDir')]
    while True:
        next_alarm = get_next_alarm_time()
        logging.info(f"Next alarm time set for {next_alarm}")
        time_to_wait = (next_alarm - datetime.now(TIMEZONE)).total_seconds()
        time.sleep(max(time_to_wait, 0))  # Sleep until the alarm time
        end_time = datetime.now(TIMEZONE) + timedelta(hours=1)  # Play songs for 1 hour
        play_songs_until_end_time(end_time, songs)

if __name__ == "__main__":
    main()
