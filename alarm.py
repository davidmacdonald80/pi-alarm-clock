#!/home/david/alarm/bin/python
# path to venv python

import time
from datetime import datetime, timedelta
from pathlib import Path
from random import choice
from subprocess import run
from phue import Bridge
from pipewire_python.controller import Controller
import logging
from zoneinfo import ZoneInfo  # For timezone handling including DST

# Setup basic logging
logging.basicConfig(filename='/home/david/alarm/alarm.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# General adjustable settings
ALARM_TIME = "6:05"  # Daily alarm time to use
VOLUME_LEVEL = 75  # volume level to set for both pactl sinks and pipewire_python player (0 - 100)
MP3_PATH = '/media/audio/got-in-2023/'  # Path to your audio library
TIMEZONE = ZoneInfo("America/Chicago")  # Local timezone
LIGHTS_BRIDGE_IP = '192.168.2.241'
BEDROOM_LIGHTS = ['Lamp', 'FarWall', 'NearWall']
LIGHT_COMMAND = {'transitiontime': 3000, 'on': True, 'bri': 254}

# Initialize Bridge for lights
try:
    bridge = Bridge(LIGHTS_BRIDGE_IP)
    # bridge.connect() # Uncomment if first-time setup is needed
except Exception as e:
    logging.error('Error connecting to Hue Bridge: ', exc_info=True)

def set_lights(on=True):
    try:
        command = LIGHT_COMMAND if on else {'on': False}
        bridge.set_light(BEDROOM_LIGHTS, command)
        logging.info(f"Lights {'on' if on else 'off'} at {datetime.now(TIMEZONE)}")
    except Exception as e:
        logging.error("Failed to control lights: ", exc_info=True)

def set_volume_for_all_sinks(volume_level):
    try:
        result = run(['pactl', 'list', 'short', 'sinks'], capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Failed to list PulseAudio sinks: {result.stderr}")
            return False
        
        sinks = result.stdout.splitlines()
        for sink in sinks:
            sink_name = sink.split('\t')[1]
            volume_command = ['pactl', 'set-sink-volume', sink_name, f'{volume_level}%']
            result = run(volume_command, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Failed to set volume for {sink_name}: {result.stderr}")
                return False
        return True
    except Exception as e:
        logging.error(f"Exception in set_volume_for_all_sinks: {e}")
        return False

def get_next_alarm_time():
    now = datetime.now(TIMEZONE)
    alarm_time = datetime.strptime(ALARM_TIME, "%H:%M").time()
    next_alarm = datetime(now.year, now.month, now.day, alarm_time.hour, alarm_time.minute, tzinfo=TIMEZONE)
    if now >= next_alarm:
        next_alarm += timedelta(days=1)
    return next_alarm

def play_song(file_path, volume_level):
    if not set_volume_for_all_sinks(volume_level):
        logging.error("Volume setting failed, skipping song play.")
        return
    try:
        audio_controller = Controller()
        audio_controller.set_config(rate=48000, channels=2, _format='f64', volume=volume_level/100, quality=11)
        audio_controller.playback(audio_filename=file_path)
        logging.info(f"Successfully played {file_path}")
    except Exception as e:
        logging.error(f"Failed to play {file_path}: {e}")

def play_songs_until_end_time(end_time, songs, volume_level):
    while datetime.now(TIMEZONE) < end_time:
        random_song = choice(songs)
        logging.info(f"Playing song: {random_song}")
        play_song(random_song, volume_level)
        time.sleep(10)  # Delay between songs, adjust as needed

def main(mp3_path):
    songs = [str(song) for song in Path(mp3_path).rglob('*.mp3') if not song.parent.match('@eaDir')]
    while True:
        next_alarm = get_next_alarm_time()
        end_time = next_alarm + timedelta(hours=2)  # Define end_time dynamically
        logging.info(f"Next alarm time set for {next_alarm}, will play until {end_time}")
        time_to_wait = (next_alarm - datetime.now(TIMEZONE)).total_seconds()
        time.sleep(max(time_to_wait, 0))  # Sleep until the alarm time
        set_lights(True)
        play_songs_until_end_time(end_time, songs, VOLUME_LEVEL)  # Pass the volume level
        set_lights(False)

if __name__ == "__main__":
    main(MP3_PATH)