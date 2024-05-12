#!/home/david/alarm/bin/python
# Path to the virtual environment's Python interpreter.

import time
from datetime import datetime, timedelta
from pathlib import Path
from random import choice
from subprocess import run
from phue import Bridge
from pipewire_python.controller import Controller
from zoneinfo import ZoneInfo  # For time zones, including DST.
from systemd import journal

# Configuration constants.
ALARM_TIME = "6:05" # Alarm time
VOLUME_LEVEL = 65 # Volume level for sinks and player (0-100)
MP3_PATH = '/media/audio/got-in-2023/' # Audio library path
TIMEZONE = ZoneInfo("America/Chicago") # Location's time zone
LIGHTS_BRIDGE_IP = '192.168.2.241' # Hue Bridge IP address
BEDROOM_LIGHTS = ['Lamp', 'FarWall', 'NearWall'] # Light group
LIGHT_COMMAND = {'transitiontime': 3000, 'on': True, 'bri': 254} 


def log_to_journal(message, level='info', exception=None):
    """
    Log messages to systemd's journal with optional exception details.

    Args:
        message (str): The message to log.
        level (str): The log level ('info', 'error', etc.).
        exception (Exception, optional): 
            The exception object to log, if any.
    """
    if exception:
        # Append exception message to the log.
        message += f" Exception: {str(exception)}"

    priority_level = {
        'emerg': journal.LOG_EMERG,
        'crit': journal.LOG_CRIT,
        'error': journal.LOG_ERR,
        'warning': journal.LOG_WARNING,
        'info': journal.LOG_INFO,
        'debug': journal.LOG_DEBUG
    }.get(level, journal.LOG_INFO)
    journal.send(message, PRIORITY=priority_level)


try:
    BRIDGE = Bridge(LIGHTS_BRIDGE_IP)
    # bridge.connect()  # Uncomment if first-time setup is needed.
except Exception as e:
    log_to_journal('Error connecting to Hue Bridge.',
                   level='error',
                   exception=e)

def set_lights(bridge, light_group, light_command, timezone, on=True):
    """
    Toggle the state of bedroom lights via the Hue Bridge.

    Args:
        on (bool): True to turn lights on, False to turn them off.
    """
    if on:
        command = light_command
    else:
        command = {'on': False}

    try:
        bridge.set_light(light_group, command)
        log_to_journal(f"Lights {'on' if on else 'off'}"\
                       f"at {datetime.now(timezone)}",
                       level='info')
    except Exception as e:
        log_to_journal("Failed to control lights.",
                       level='error',
                       exception=e)


def check_volume_input(volume):
    """
    Verify volume given is within constraints
    """
    if 0 <= volume <= 100:
        return True
    else:
        return False

def set_volume_for_all_sinks(volume_level):
    """Set the volume level for all PulseAudio sinks.

    Args:
        volume_level (int): Volume level in percentage (0-100).
    """
    try:
        result = run(['pactl', 'list', 'short', 'sinks'],
                     capture_output=True,
                     text=True)
        if result.returncode != 0:
            log_to_journal("Failed to list PulseAudio sinks:"\
                           f" {result.stderr}", level='error')
            return False
        
        sinks = result.stdout.splitlines()
        for sink in sinks:
            sink_name = sink.split('\t')[1]
            if(check_volume_input(volume_level)):
                volume_command = ['pactl',
                                'set-sink-volume',
                                sink_name,
                                f'{volume_level}%']
                result = run(volume_command, capture_output=True, text=True)
            else:
                return False
            if result.returncode != 0:
                log_to_journal(f"Failed to set volume for {sink_name}:"\
                               f" {result.stderr}", level='error')
                return False
        return True
    except Exception as e:
        log_to_journal("Exception in set_volume_for_all_sinks.",
                       level='error',
                       exception=e)
        return False


def get_next_alarm_time(timezone, alarm_time):
    """Calculate the next scheduled alarm time.

    Returns:
        datetime: The next alarm time 
            considering the current time and time zone.
    """
    now = datetime.now(timezone)
    alarm_time = datetime.strptime(alarm_time, "%H:%M").time()
    next_alarm = datetime(now.year,
                          now.month,
                          now.day,
                          alarm_time.hour,
                          alarm_time.minute,
                          tzinfo=timezone)
    if now >= next_alarm:
        next_alarm += timedelta(days=1)
    return next_alarm


def play_song(file_path, volume_level):
    """Play a song using pipewire with specified volume level.

    Args:
        file_path (str): Path to the song file.
        volume_level (int): Volume level (0-100).
    """
    if not set_volume_for_all_sinks(volume_level):
        log_to_journal("Volume setting failed, skipping song play.",
                        level='error')
        return
    try:
        audio_controller = Controller()
        audio_controller.set_config(rate=48000,
                                    channels=2,
                                    _format='f64',
                                    volume=volume_level/100,
                                    quality=11)
        audio_controller.playback(audio_filename=file_path)
        log_to_journal(f"Successfully played {file_path}", level='info')
    except Exception as e:
        log_to_journal(f"Failed to play {file_path}.",
                       level='error',
                       exception=e)


def play_songs_until_end_time(end_time, songs, volume_level, timezone):
    """Play songs until a specified end time is reached.

    Args:
        end_time (datetime): Time to stop playing songs.
        songs (list of str): List of song paths.
        volume_level (int): Volume level (0-100).
    """
    while datetime.now(timezone) < end_time:
        random_song = choice(songs)
        log_to_journal(f"Playing song: {random_song}", level='info')
        play_song(random_song, volume_level)
        time.sleep(10)  # Delay between songs.


def main(mp3_path, light_group, bridge, timezone,
         volume_level, alarm_time, light_command):
    """Main function to handle alarm scheduling and song playing.

    Args:
        mp3_path (str): Path to the directory containing MP3 files.
    """
    # I store my media on a Synology device.
    # Exclude thumbnail directories that are identified by '@eaDir'
    songs = [str(song) for song in Path(mp3_path).rglob('*.mp3')
            if not song.parent.match('@eaDir')]
    while True:
        try:
            next_alarm = get_next_alarm_time(timezone=timezone,
                                            alarm_time=alarm_time)
            end_time = next_alarm + timedelta(hours=2)  # Play for 2 hours.
            log_to_journal(f"Next alarm time set for {next_alarm},"\
                        f" will play until {end_time}", level='info')
            time_to_wait = (
                next_alarm - datetime.now(timezone)).total_seconds()
            time.sleep(max(time_to_wait, 0))  # Sleep until the alarm time.
            set_lights(bridge, light_group, light_command, timezone, True)
            play_songs_until_end_time(end_time, songs, volume_level, timezone)
            set_lights(bridge, light_group, light_command, timezone, False)
        except Exception as e:
            log_to_journal("An error occured in main loop.",
                           level='error', exception=e)
            set_lights(bridge, light_group, light_command, timezone, False) 


if __name__ == "__main__":
    main(mp3_path=MP3_PATH, light_group=BEDROOM_LIGHTS, bridge=BRIDGE,
         timezone=TIMEZONE, volume_level=VOLUME_LEVEL, alarm_time=ALARM_TIME,
         light_command=LIGHT_COMMAND)
