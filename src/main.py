
gc.collect()

import time

#t=time.gmtime()
#print(f"Time is : {t}")
#if t[0] < 2022:
try:
  import ntptime
  ntptime.settime()  # Synchronise the system time using NTP
except:
  pass

import machine
import nextstage
import errno
import umqttsimple
import json
#import ssl

#5 mins
future_try = 300000
def try_in_future():
  if doSleep:
   machine.deepsleep(future_try)
  pass

def main_shutdown():
  if doLocal:
    localmqtt.disconnect()

  print("Sleeping...")
  try_in_future()


def main_loop():
  start_time = time.time()
  counter = 0
  while True:
    # calls the callback.
    localmqtt.check_msg()
    if (time.time() - start_time) > 10:
      # tap out after 10 second.
      main_shutdown()
      sleep(1)
      counter += 1


# listening for battery
# also now acks because combine cloud into local...
def local_recv(topic,msg):
  
  print(f"locally received : {topic}\n{msg}")
  device = topic.decode("utf8").split("/")[1]
  batt = int(msg)

  if device == "tablet":
    print("Got one...")
    channel = 1
  elif device == "phone":
    print("Got two...?")
    channel = 3
  else:
    return
  if batt > 60:
    print(f"turning OFF battery for {device}")
    nextstage.meross_toggle(localmqtt,channel,False,fake=True)
    nextstage.meross_toggle(localmqtt,channel,False,fake=True)
    #sleep(5)
    #nextstage.meross_toggle(channel,False)
    #sleep(5)

  elif batt < 40:
    print(f"turning ON battery for {device}")
    nextstage.meross_toggle(localmqtt,channel,True,fake=True)
    nextstage.meross_toggle(localmqtt,channel,True,fake=True)
    #sleep(5)
    #nextstage.meross_toggle(channel,True)
    #sleep(5)

# start here
try:
  #client.check_msg()

  # print("Logging In...")
  # print()
  # nextstage.meross_log_in()
  # print("Device List...")
  # print()
  # nextstage.meross_device_list()
  #print("Hub List...")
  #print()
  #nextstage.meross_hub_list()

  #connect and subscribe to cloud mqtt
  #nextstage.setupMqtt()
  #connect and subscribe to local mqtt
  doLocal = True
  doSleep = True
  if doLocal:
    # with open('ca.crt') as f:
    #     ca_data = f.read()
    localmqtt = umqttsimple.MQTTClient("esp32","192.168.0.54",port=8883,ssl=True)
    localmqtt.set_callback(local_recv)
    localmqtt.connect()
    localmqtt.publish("brave/esp32/heartbeat",' '.join([str(s) for s in time.gmtime()]),retain=True)
    localmqtt.publish("brave/esp32/heartbeat",' '.join([str(s) for s in time.gmtime()]),retain=True)

    time.sleep(5)
    
    localmqtt.subscribe("brave/+/battery")
    

    #nextstage.meross_toggle(localmqtt,4,False,fake=True)
    #time.sleep(5)
    #nextstage.meross_toggle(localmqtt,4,True,fake=True)

    main_loop()
  #1 = tablet
  #2 = lamp
  #3 = phone
  #4 = computer
  #5 = esp32
  #nextstage.meross_toggle(1,False)

  #nextstage.mqttclient.disconnect()

  #nextstage.mqttclient.wait_msg()
  # this ensures both 

# let the callback shut it all down

except Exception as e:
    print("ERROR!")
    import sys
    sys.print_exception(e)




  #print(f"About to destroy timers and sleep/disconect\nexpectacks={nextstage.expectAcks}")
  #for k in nextstage.our_timers:
  #  nextstage.our_timers[k].destroy()


  #nextstage.mqttclient.disconnect()
