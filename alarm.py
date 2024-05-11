#!/home/david/alarm/bin/python
# path to venv python

import time
from datetime import datetime, timedelta
from pathlib import Path
from random import choice
from subprocess import run
from phue import Bridge
from pipewire_python.controller import Controller
from zoneinfo import ZoneInfo  # For timezone handling including DST
from systemd import journal

# General adjustable settings
ALARM_TIME = "6:05"  # Daily alarm time to use
VOLUME_LEVEL = 75  # volume level to set for both pactl sinks and pipewire_python player (0 - 100)
MP3_PATH = '/media/audio/got-in-2023/'  # Path to your audio library
TIMEZONE = ZoneInfo("America/Chicago")  # Local timezone
LIGHTS_BRIDGE_IP = '192.168.2.241'
BEDROOM_LIGHTS = ['Lamp', 'FarWall', 'NearWall']
LIGHT_COMMAND = {'transitiontime': 3000, 'on': True, 'bri': 254}

def log_to_journal(message, level='info', exception=None):
    """Log messages to systemd's journal

    Args:
        message (str): The message to log.
        level (str): The log level ('info', 'error', etc.).
        exception (Exception, optional): The exception object to log, if any.
    """
    if exception:
        message += f" Exception: {str(exception)}" # Append exception message
    
    priority_level = {
        'emerg': journal.LOG_EMERG,
        'crit': journal.LOG_CRIT,
        'error': journal.LOG_ERR,
        'warning': journal.LOG_WARNING,
        'info': journal.LOG_INFO,
        'debug': journal.LOG_DEBUG
    }.get(level, journal.LOG_INFO) # Default to info if the level not found

# Initialize Bridge for lights
try:
    bridge = Bridge(LIGHTS_BRIDGE_IP)
    # bridge.connect() # Uncomment if first-time setup is needed
except Exception as e:
    log_to_journal('Error connecting to Hue Bridge.', level='error', exc_info=True)

def set_lights(on=True):
    try:
        command = LIGHT_COMMAND if on else {'on': False}
        bridge.set_light(BEDROOM_LIGHTS, command)
        log_to_journal(f"Lights {'on' if on else 'off'} at {datetime.now(TIMEZONE)}", level='info')
    except Exception as e:
        log_to_journal("Failed to control lights.", level='error', exc_info=True)

def set_volume_for_all_sinks(volume_level):
    try:
        result = run(['pactl', 'list', 'short', 'sinks'], capture_output=True, text=True)
        if result.returncode != 0:
            log_to_journal(f"Failed to list PulseAudio sinks: {result.stderr}", level='error')
            return False
        
        sinks = result.stdout.splitlines()
        for sink in sinks:
            sink_name = sink.split('\t')[1]
            volume_command = ['pactl', 'set-sink-volume', sink_name, f'{volume_level}%']
            result = run(volume_command, capture_output=True, text=True)
            if result.returncode != 0:
                log_to_journal(f"Failed to set volume for {sink_name}: {result.stderr}", level='error')
                return False
        return True
    except Exception as e:
        log_to_journal(f"Exception in set_volume_for_all_sinks:", level='error', exception=e)
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
        log_to_journal("Volume setting failed, skipping song play.", level='error')
        return
    try:
        audio_controller = Controller()
        audio_controller.set_config(rate=48000, channels=2, _format='f64', volume=volume_level/100, quality=11)
        audio_controller.playback(audio_filename=file_path)
        log_to_journal(f"Successfully played {file_path}", level='info')
    except Exception as e:
        log_to_journal(f"Failed to play {file_path}:", level='error', exception=e)

def play_songs_until_end_time(end_time, songs, volume_level):
    while datetime.now(TIMEZONE) < end_time:
        random_song = choice(songs)
        log_to_journal(f"Playing song: {random_song}", level='info')
        play_song(random_song, volume_level)
        time.sleep(10)  # Delay between songs, adjust as needed

def main(mp3_path):
    songs = [str(song) for song in Path(mp3_path).rglob('*.mp3') if not song.parent.match('@eaDir')]
    while True:
        next_alarm = get_next_alarm_time()
        end_time = next_alarm + timedelta(hours=2)  # Define end_time dynamically
        log_to_journal(f"Next alarm time set for {next_alarm}, will play until {end_time}", level='info')
        time_to_wait = (next_alarm - datetime.now(TIMEZONE)).total_seconds()
        time.sleep(max(time_to_wait, 0))  # Sleep until the alarm time
        set_lights(True)
        play_songs_until_end_time(end_time, songs, VOLUME_LEVEL)  # Pass the volume level
        set_lights(False)

if __name__ == "__main__":
    main(MP3_PATH)