
---
# d32 esp lolin mqtt auto power
## Mqtt Explorer
* git clone mqtt explorer
* edit package.json in src dir to replace --arch x64 with --arch armv7l
* yarn, yarn build, yarn start

## Retext viewer
*  ~/.config/ReText project/ReText.conf
* defaultPreviewState=live-preview

## Usb->Uart serial connection
* dmesg | grep tty
* screen /dev/ttyUSB0 115200

## MicroPython WebRepl
* https://github.com/micropython/webrepl
* file:///home/pi/esp32/webrepl/webrepl.html#192.168.0.71:8266/
* No reason to use this, prefer terminal below

## MicroPython file access via terminal
### connecting
rshell --buffer-size=30 -p '/dev/ttyUSB0' -a  
### how it works
all files are accessible under /pyboard  other directories are considered local.  
ls -l /pyboard
### compiling checking for errors by soft reboot
repl  
ctrl+d  
### uploading changes
rsync src /pyboard
## MQTT Node Red
* topic/subtopic/subtopic
### qos detail
* 0  = one packet is sent, but its unreliable , at most one
* 1 =  many packets are sent, to ensure delivery, at least one
*  2 = slow confirmation is performed on top of tcp stack, excatly one
TCP comes with error correction and retransmission for lost packets only for the duration of a session. If the TCP session gets dropped (like when you reboot a machine) then all the TCP buffers are gone and you lose data.

MQTT QOS 1 and QOS 2 will not lose data, even when the publisher, subscriber, or mqtt broker reboots. It does this by writing messages to disk or some other non volatile place that can survive a reboot.

### client status saved in mqtt broker
using Birth,Death,Will messages, you can make the other clients know when this device is online/offline etc.

---
# Ideas 
* send battery % from phone to mqtt using macrodroid?
* read battery % on esp32
* involve watch status updates
* pizero is the mqtt server
* phones publish on topic brave/phone/battery
* tablet publish on topic brave/tablet/battery
* esp32 subscribes to /brave/+/battery
* esp32 goes into deep sleep 5 mins after running/checking for messages
