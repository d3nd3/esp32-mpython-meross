# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

print("Running boot.py...")

import network
from creds import lan_ssid,lan_pw
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.ifconfig(('192.168.0.71','255.255.255.0','192.168.0.1','1.1.1.1'))
try:
  wlan.connect(lan_ssid,lan_pw)
except OSError as e:
  print(f"connection state is {wlan.isconnected()}")

if wlan.isconnected == False:
  print("trying again in 5 mins to connect to wifi")
  machine.deepsleep(300000)
print("connected to wifi!")
#import webrepl
#webrepl.start()
