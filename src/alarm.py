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
from threading import Thread, Event

class AlarmClock:
    def __init__(self, alarm_time, only_weekdays, volume_level):
        self.alarm_time = alarm_time
        self.only_weekdays = only_weekdays
        self.volume_level = volume_level
        self.mp3_path = '/media/audio/got-in-2023'
        self.timezone = ZoneInfo("America/Chicago")
        self.lights_bridge_ip = '192.168.2.241'
        self.bedroom_lights = ['Lamp', 'FarWall', 'NearWall']
        self.light_command = {'transitiontime': 3000, 'on': True, 'bri': 254}
        self.bridge = self.initialize_bridge()
    
    def initialize_bridge(self):
        """Initialize the Hue Bridge connection."""
        try:
            return Bridge(self.lights_bridge_ip)
        except Exception as e:
            self.log_to_journal('Error connecting to Hue Bridge',
                                level='error',
                                exception=e)
            return None

    def log_to_journal(self, message, level='info', exception=None):
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

    def next_weekday(self, start_date):
        """ Return the next weekday date from the given start date."""
        while start_date.weekday() >= 5:
            start_date += timedelta(days=1)
        return start_date

    def get_next_alarm_time(self):
        """
        Calculate the next weekday alarm time
        considering the current time and timezone.
        """
        alarm_time = datetime.strptime(self.alarm_time, "%H:%M").time()
        now = datetime.now(self.timezone)
        next_alarm = datetime(now.year, now.month, now.day, alarm_time.hour,
                            alarm_time.minute, tzinfo=self.timezone)
        if now >= next_alarm:
            next_alarm += timedelta(days=1)
        if self.only_weekdays:
            next_alarm = self.next_weekday(next_alarm)
        return next_alarm

    def set_lights(self, on=True):
        """
        Toggle the state of bedroom lights via the Hue Bridge.
        Args:
            on (bool): True to turn lights on, False to turn them off.
        """
        if self.bridge is None:
            self.log_to_journal("Bridge not intialized.", level='error')
            return
        command = self.light_command if on else {'on': False}
        # if on:
        #     command = self.light_command
        # else:
        #     command = {'on': False}
        try:
            self.bridge.set_light(self.bedroom_lights, command)
            self.log_to_journal(f"Lights {'on' if on else 'off'}"\
                        f"at {datetime.now(self.timezone)}",
                        level='info')
        except Exception as e:
            self.log_to_journal("Failed to control lights.",
                        level='error',
                        exception=e)

    def check_volume_input(self, vl):
        """
        Verify volume given is within constraints
        """
        if 0 <= vl <= 100:
            return True
        else:
            return False

    def set_volume_for_all_sinks(self):
        """
        Set the volume level for all PulseAudio sinks.
        Args:
            volume_level (int): Volume level in percentage (0-100).
        """
        try:
            result = run(['pactl', 'list', 'short', 'sinks'],
                        capture_output=True,
                        text=True)
            if result.returncode != 0:
                self.log_to_journal("Failed to list PulseAudio sinks:"\
                            f" {result.stderr}", level='error')
                return False

            sinks = result.stdout.splitlines()
            for sink in sinks:
                sink_name = sink.split('\t')[1]
                if(self.check_volume_input(vl=self.volume_level)):
                    volume_command = ['pactl',
                                    'set-sink-volume',
                                    sink_name,
                                    f'{self.volume_level}%']
                    result = run(volume_command,
                                 capture_output=True,
                                 text=True)
                else:
                    return False
                if result.returncode != 0:
                    self.log_to_journal(f"Failed to set volume for "\
                                        f"{sink_name}: {result.stderr}",
                                        level='error')
                    return False
            return True
        except Exception as e:
            self.log_to_journal("Exception in set_volume_for_all_sinks.",
                        level='error',
                        exception=e)
            return False

    def play_song(self, file_path):
        """
        Play a song using pipewire with specified volume level.
        Args:
            file_path (str): Path to the song file.
            volume_level (int): Volume level (0-100).
        """
        if not self.set_volume_for_all_sinks():
            self.log_to_journal("Volume setting failed, skipping song play.",
                            level='error')
            return
        try:
            audio_controller = Controller()
            audio_controller.set_config(rate=48000,
                                        channels=2,
                                        _format='f64',
                                        volume=self.volume_level/100,
                                        quality=11)
            audio_controller.playback(audio_filename=file_path)
            self.log_to_journal(f"Successfully played {file_path}",
                                level='info')
        except Exception as e:
            self.log_to_journal(f"Failed to play {file_path}.",
                        level='error',
                        exception=e)

    def play_songs_until_end_time(self, end_time):
        """
        Play songs until a specified end time is reached.
        Args:
            end_time (datetime): Time to stop playing songs.
            songs (list of str): List of song paths.
            volume_level (int): Volume level (0-100).
        """
        songs = [str(song) for song in Path(self.mp3_path).rglob('*.mp3')
                if not song.parent.match('@eaDir')]
        while datetime.now(self.timezone) < end_time:
            random_song = choice(songs)
            self.log_to_journal(f"Playing song: {random_song}", level='info')
            self.play_song(random_song)
            time.sleep(10)  # Delay between songs.

    def main(self):
        """
        Main function to handle alarm scheduling and song playing.
        Args:
            mp3_path (str): Path to the directory containing MP3 files.
        """
        # I store my media on a Synology device.
        # Exclude thumbnail directories that are identified by '@eaDir'
        while True:
            try:
                next_alarm = self.get_next_alarm_time()
                end_time = next_alarm + timedelta(hours=2)
                self.log_to_journal(f"Next alarm time set for {next_alarm},"\
                            f" will play until {end_time}", level='info')
                time_to_wait = (
                    next_alarm - datetime.now(self.timezone)).total_seconds()
                time.sleep(max(time_to_wait, 0))
                self.set_lights(True)
                self.play_songs_until_end_time(end_time)
                self.set_lights(False)
            except Exception as e:
                self.log_to_journal("An error occured in main loop.",
                            level='error', exception=e)
                self.set_lights(False) 


if __name__ == "__main__":
    threads = []
    clocks = []
    clocks.append(AlarmClock(alarm_time="6:05", only_weekdays=True, volume_level=70))
    # clocks.append(AlarmClock(alarm_time="23:17", only_weekdays=True, volume_level=85))

    for clock in clocks:
        thread = Thread(target=clock.main)
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
