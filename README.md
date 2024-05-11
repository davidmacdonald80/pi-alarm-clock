# pi-alarm-clock

Pretty simple alarm clock.
If you have PhillipsHue lights with a Bridge, it will turn them on for you when the alarm goes off with a 5 min transition.
I've got the basic ones that don't do color. I may try the color ones in the future.

You can put the systemd service file in: (there are a few other spots it can go)
~/.config/systemd/user/default.target.wants/
then:
systemctl --user enable --now alarm.service

if you make any changes to the alarm.py that you want updated in the service:
systemctl --user restart alarm.service
