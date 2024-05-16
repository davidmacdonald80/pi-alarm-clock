import json
from pathlib import Path
from alarm_clock import AlarmClock  # Assuming your class is in alarm_clock.py

def get_user_input(prompt, default=None):
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    user_input = input(prompt)
    return user_input if user_input else default

def main():
    settings = AlarmClock.load_settings()
    if not settings:
        print("No settings found. Let's set them up.")
        mp3_path = get_user_input("Enter the path to MP3 files", 
                                  '/media/audio/got-in-2023')
        timezone = get_user_input("Enter your timezone", 'America/Chicago')
        lights_bridge_ip = get_user_input("Enter the Hue Bridge IP address", 
                                          '192.168.2.241')
        bedroom_lights = get_user_input(
            "Enter bedroom light names (comma-separated)", 'Lamp,FarWall,NearWall')
        light_command = get_user_input(
            "Enter light command (JSON format)", 
            '{"transitiontime": 3000, "on": True, "bri": 254}')
        settings = {
            'mp3_path': mp3_path,
            'timezone': timezone,
            'lights_bridge_ip': lights_bridge_ip,
            'bedroom_lights': bedroom_lights.split(','),
            'light_command': json.loads(light_command)
        }
    else:
        print("Existing settings found.")
        for key, value in settings.items():
            if key in ['alarm_time', 'only_weekdays', 'volume_level', 
                       'alarm_duration']:
                continue
            edit = get_user_input(f"Edit {key}? (y/n)", 'n')
            if edit.lower() == 'y':
                settings[key] = get_user_input(f"Enter new value for {key}", 
                                               value)

    alarm_time = get_user_input("Enter the alarm time (HH:MM)", 
                                settings.get('alarm_time'))
    only_weekdays = get_user_input("Only weekdays? (true/false)", 
                                   settings.get('only_weekdays'))
    volume_level = get_user_input("Enter volume level (0-100)", 
                                  settings.get('volume_level'))
    alarm_duration = get_user_input(
        "Enter alarm duration (e.g., 2 hours, 30 minutes)", 
        settings.get('alarm_duration'))

    alarm_clock = AlarmClock(alarm_time, only_weekdays, volume_level, 
                             alarm_duration, mp3_path=settings['mp3_path'], 
                             timezone=settings['timezone'], 
                             lights_bridge_ip=settings['lights_bridge_ip'], 
                             bedroom_lights=settings['bedroom_lights'], 
                             light_command=settings['light_command'])
    alarm_clock.save_settings()
    print("Settings saved.")

if __name__ == "__main__":
    main()