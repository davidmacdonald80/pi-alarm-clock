#!/usr/bin/env python

import traceback
import time
from phue import Bridge
import schedule

try:
    b = Bridge('192.168.2.241')
    #b.connect()
except Exception as e:
    print('There was an error: ', e)
    traceback.print_exc()
bedRoom = ['Lamp', 'FarWall', 'NearWall']
# 300 - 30 seconds, 600 - 60sec, 3000 - 5min, 9000 - 15min
command = {'transitiontime' : 3000, 'on' : True, 'bri' : 254,}

def onJobMorning():
    b.set_light(bedRoom, command)
# b.set_light('Lamp', 'bri', 254) # 1-254 levels
# b.set_light('Lamp', 'on', True) #turn lamp light on

#b.set_light(['Lamp', 'FarWall', 'NearWall'], 'on', True) #turn all lights on

def offJob():
    b.set_light(bedRoom, 'on', False)

schedule.every().monday.at('06:05').do(onJobMorning)
schedule.every().tuesday.at('06:05').do(onJobMorning)
schedule.every().wednesday.at('06:05').do(onJobMorning)
schedule.every().thursday.at('06:05').do(onJobMorning)
schedule.every().friday.at('06:05').do(onJobMorning)

schedule.every().monday.at('07:30').do(offJob)
schedule.every().tuesday.at('07:30').do(offJob)
schedule.every().wednesday.at('07:30').do(offJob)
schedule.every().thursday.at('07:30').do(offJob)
schedule.every().friday.at('07:30').do(offJob)

schedule.every().monday.at('16:45').do(onJobMorning)
schedule.every().tuesday.at('16:45').do(onJobMorning)
schedule.every().wednesday.at('16:45').do(onJobMorning)
schedule.every().thursday.at('16:45').do(onJobMorning)
schedule.every().friday.at('16:45').do(onJobMorning)

schedule.every().monday.at('17:15').do(offJob)
schedule.every().tuesday.at('17:15').do(offJob)
schedule.every().wednesday.at('17:15').do(offJob)
schedule.every().thursday.at('17:15').do(offJob)
schedule.every().friday.at('17:15').do(offJob)

# schedule.every().thursday.at('21:00').do(onJobMorning)

#schedule.every().tuesday.at('20:15').do(offJob)

while True:
    try:
        schedule.run_pending()
    except Exception as e:
        print('Error occured: ', e)
        traceback.print_exc()
    time.sleep(1)
