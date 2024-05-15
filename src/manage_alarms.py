import json
from alarm import AlarmClock

SETTINGS_FILE = 'alarm_settings.json'

def load_settings():
    """Load alarm settings from a JSON file."""
    try:
        with open(SETTINGS_FILE, 'r') as f:
            alarm_dicts = json.load(f)
            return [AlarmClock(**alarm_dict) for alarm_dict in alarm_dicts]
    except FileNotFoundError:
        return []

def save_settings(alarms):
    """Save alarm settings to a JSON file."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump([alarm.to_dict() for alarm in alarms], f, indent=4)

def list_alarms(alarms):
    """List all alarms."""
    for idx, alarm in enumerate(alarms):
        print(f"{idx}: Time: {alarm.alarm_time}, Only Weekdays: {alarm.only_weekdays}, Volume: {alarm.volume_level}")

def add_alarm():
    """Add a new alarm."""
    alarm_time = input("Enter alarm time (HH:MM): ")
    only_weekdays = input("Only weekdays (yes/no): ").lower() == 'yes'
    volume_level = int(input("Enter volume level (0-100): "))
    return AlarmClock(alarm_time, only_weekdays, volume_level)

def modify_alarm(alarm):
    """Modify an existing alarm."""
    alarm.alarm_time = input(f"Enter alarm time (HH:MM) [{alarm.alarm_time}]: ") or alarm.alarm_time
    only_weekdays = input(f"Only weekdays (yes/no) [{alarm.only_weekdays}]: ").lower()
    alarm.only_weekdays = (only_weekdays == 'yes') if only_weekdays else alarm.only_weekdays
    volume_level = input(f"Enter volume level (0-100) [{alarm.volume_level}]: ")
    alarm.volume_level = int(volume_level) if volume_level else alarm.volume_level

def delete_alarm(alarms):
    """Delete an existing alarm."""
    list_alarms(alarms)
    idx = int(input("Enter the index of the alarm to delete: "))
    if 0 <= idx < len(alarms):
        alarms.pop(idx)
    else:
        print("Invalid index.")

def manage_alarms(alarms):
    """Manage alarms before starting the alarm threads."""
    while True:
        print("\nAlarm Management")
        print("1. List alarms")
        print("2. Add alarm")
        print("3. Modify alarm")
        print("4. Delete alarm")
        print("5. Start alarms")
        choice = input("Choose an option: ")

        if choice == '1':
            list_alarms(alarms)
        elif choice == '2':
            alarms.append(add_alarm())
        elif choice == '3':
            list_alarms(alarms)
            idx = int(input("Enter the index of the alarm to modify: "))
            if 0 <= idx < len(alarms):
                modify_alarm(alarms[idx])
            else:
                print("Invalid index.")
        elif choice == '4':
            delete_alarm(alarms)
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")

        # Save the updated alarms after each modification
        save_settings(alarms)

if __name__ == "__main__":
    alarms = load_settings()
    manage_alarms(alarms)
    save_settings(alarms)