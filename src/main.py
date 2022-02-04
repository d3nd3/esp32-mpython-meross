
gc.collect()

import time

t=time.gmtime()
print(f"Time is : {t}")
if t[0] < 2022:
  import ntptime
  ntptime.settime()  # Synchronise the system time using NTP

import machine
import nextstage
import errno
import umqttsimple
#5 mins
future_try = 300000
def try_in_future():
  if doSleep:
   machine.deepsleep(future_try)
  pass

got_tablet = False
got_phone = False
def local_recv(topic,msg):
  global got_tablet, got_phone
  print(f"locally received : {topic}\n{msg}")
  device = topic.decode("utf8").split("/")[1]
  batt = int(msg)

  if device == "tablet":
    got_tablet = True
    channel = 1
  elif device == "phone":
    got_phone = True
    channel = 3
  else:
    return
  if batt > 62:
    print(f"turning OFF battery for {device}")
    nextstage.meross_toggle(channel,False)
    #sleep(5)
    #nextstage.meross_toggle(channel,False)
    #sleep(5)

  elif batt < 38:
    print(f"turning ON battery for {device}")
    nextstage.meross_toggle(channel,True)
    #sleep(5)
    #nextstage.meross_toggle(channel,True)
    #sleep(5)
  else:
    return

try:
  #client.check_msg()

  print("Logging In...")
  print()
  nextstage.meross_log_in()
  print("Device List...")
  print()
  nextstage.meross_device_list()
  #print("Hub List...")
  #print()
  #nextstage.meross_hub_list()

  #connect and subscribe to cloud mqtt
  nextstage.setupMqtt()
  #connect and subscribe to local mqtt
  doLocal = True
  doSleep = True
  if doLocal:
    localmqtt = umqttsimple.MQTTClient("esp32","192.168.0.54",port=1883)
    localmqtt.set_callback(local_recv)
    localmqtt.connect()
    localmqtt.subscribe("brave/+/battery")
  #1 = tablet
  #2 = lamp
  #3 = phone
  #4 = computer
  #5 = esp32
  #nextstage.meross_toggle(1,False)

  #nextstage.mqttclient.disconnect()

  #nextstage.mqttclient.wait_msg()
  while True and doLocal:
    nextstage.mqttclient.check_msg()
    localmqtt.check_msg()

    if got_phone and got_tablet and nextstage.expectAcks == 0:
      break
  print(f"About to destroy timers and sleep/disconect\nexpectacks={nextstage.expectAcks}")
  for k in nextstage.our_timers:
    nextstage.our_timers[k].destroy()

  if doLocal:
    localmqtt.disconnect()
  nextstage.mqttclient.disconnect()
  """
  last_message = 0
  message_interval = 5
  counter = 0
  while True:
    nextstage.mqttclient.check_msg()
    if (time.time() - last_message) > message_interval:
      nextstage.meross_toggle(1)
      last_message = time.time()
      counter += 1
  """
except Exception as e:
  print("ERROR!")
  import sys
  sys.print_exception(e)

print("Sleeping...")
try_in_future()


