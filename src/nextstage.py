
print("next stage lol")
#sleep
import time
#mqtt
from umqttsimple import MQTTClient

import micropython
import network
import urequests
from urlencode import urlencode
import random
import gc
import json
import md53
import ubinascii
import machine

#create this file yourself to make it work.
from creds import email,password,cached_creds

#client_id = ubinascii.hexlify(machine.unique_id())
#mqtt_server = "192.168.0.54"
mqtt_server = None
topic_sub = b'notification'
#creds={
#"token":"9e8dc2d933ba9e0839e94132ea168fad4ffc1ec44a90130e5ed052e4ce9e279f"
#}
creds = None

uuid = None
client_id = None
app_id = None
mqtt_pw = None

def randomNonce(len,lower=False):
  if not lower:
    uppercase_l = [chr(i) for i in range(ord('A'),ord('Z')+1)]
  else:
    uppercase_l = [chr(i) for i in range(ord('a'),ord('z')+1)]
  digits_l = [chr(i) for i in range(ord('0'),ord('9')+1)]
  return ''.join(random.choice(uppercase_l + digits_l) for _ in range(len))

def uuid4():
  random_string = ''
  random_str_seq = "0123456789abcdefghijklmnopqrstuvwxyz"
  uuid_format = [8, 4, 4, 4, 12]
  for n in uuid_format:
    for i in range(0,n):
      random_string += str(random_str_seq[random.randint(0, len(random_str_seq) - 1)])
    if n != 12:
      random_string += '-'
  return random_string

"""
{
    "header": {
        "messageId": "404ba38ca42067516d290a810c0bfb97",
        "namespace": "Appliance.Control.ToggleX",
        "method": "SETACK",
        "payloadVersion": 1,
        "from": "/appliance/2007240381412190820648e1e926a731/publish",
        "timestamp": 1643928723,
        "timestampMs": 477,
        "sign": "1e5fc378ba98a14ce67967f1e3f3c52b",
    },
    "payload": {},
}
"""

expectAcks = 0
# we got an Ack!
def mqttReceive(topic, msg):
  global expectAcks
  print(f"from mqtt received : {topic}\n{msg}")
  data = json.loads(msg.decode("utf8"))
  if expectAcks and data["header"]["method"] == "SETACK":
    expectAcks -= 1

#depends client_id and mqtt_server and user_id and mqtt_pw
def setupMqtt():
  global mqttclient
  mqttclient = MQTTClient(client_id, mqtt_server,user=creds["user_id"],password=mqtt_pw,ssl=True,port=443 )
  mqttclient.set_callback(mqttReceive)
  mqttclient.connect()
  mqttclient.subscribe(f"/app/{creds['user_id']}-{app_id}/subscribe")
  #mqttclient.subscribe("#")
  print("connected mqtt")


#creates token,key,user_id,user_email,issued_on
def meross_log_in():
  global creds
  creds = cached_creds
  if creds is not None:
    generate_client_and_app_id()
    generate_mqtt_password()
    return
  r = meross_post("v1/Auth/Login")
  response_data = r["data"]
  creds = {
    "token": response_data["token"],
    "key": response_data["key"],
    "user_id": response_data["userid"],
    "user_email": response_data["email"],
    "issued_on": time.gmtime()
  }

  generate_client_and_app_id()
  generate_mqtt_password()

def meross_log_out():
  meross_post("v1/Profile/logout")
  creds=None

#creates mqtt_server and uuid
def meross_device_list():
  global uuid, mqtt_server
  r = meross_post("v1/Device/devList")
  uuid = r["data"][0]["uuid"]
  mqtt_server = r["data"][0]["domain"]
"""
{
    "sysStatus": 0,
    "data": [
        {
            "userDevIcon": "",
            "iconType": 1,
            "skillNumber": "",
            "devName": "Smart Surge Protector",
            "cluster": 2,
            "domain": "mqtt-eu-2.meross.com",
            "reservedDomain": "mqtt-eu-2.meross.com",
            "channels": [
                {},
                {"devIconId": "device001", "devName": "Switch 1", "type": "Switch"},
                {"devIconId": "device001", "devName": "Switch 2", "type": "Switch"},
                {"devIconId": "device001", "devName": "Switch 3", "type": "Switch"},
                {"devIconId": "device001", "devName": "Switch 4", "type": "Switch"},
                {"devIconId": "device001", "devName": "USB", "type": "USB"},
            ],
            "devIconId": "device033_uk",
            "uuid": "2007240381412190820648e1e926a731",
            "region": "eu",
            "onlineStatus": 1,
            "fmwareVersion": "3.1.2",
            "bindTime": 1635206496,
            "subType": "uk",
            "hdwareVersion": "3.0.0",
            "deviceType": "mss425f",
        }
    ],
    "apiStatus": 0,
    "info": "Success",
    "timeStamp": 1643852464,
}
"""
#from machine import Timer
#virtual timer
#t = Timer(-1)
#timer.init(period=3000,mode=Timer.PERIODIC,callback=lambda t:print("hi"))
#timer.init(period=3000,mode=Timer.ONE_SHOT,callback=lambda t:print("hi"))

from machine import Timer

our_timers = {}
class handleAckTimer():
  def __init__(self,dur,channel,state,timer_id,broker,fake):
    self.timer = Timer(-1)
    self.timer.init(period=dur,mode=Timer.ONE_SHOT,callback=self.cb)
    self.channel = channel
    self.state = state
    self.timer_id = timer_id
    self.fake = fake
    self.broker = broker
  def cb(self,timer):
    print("Timer EXPIRED!!!!!!")
    global expectAcks
    #send out another toggle
    meross_toggle(self.broker,self.channel,self.state,self.fake)
    #decrement becos the last one is lost, assumed.
    expectAcks -=1
    print(f"Required Acks = {expectAcks}")
    del our_timers[self.timer_id]
  def destroy(self):
    self.timer.deinit()

def meross_toggle(mqttcl,channel,state,fake=False):
  global expectAcks
  msg = meross_mqtt_build(channel,state,fake)
  #now publish to /appliance/<client_id>/subscribe
  
  # {uuid} vs 2007240381412190820648e1e926a731(local)
  mqttcl.publish(f"/appliance/2007240381412190820648e1e926a731/subscribe",msg)
  if not fake:
    expectAcks +=1
    print(f"Required Acks = {expectAcks}")
    timer_id = randomNonce(16)
    our_timers[timer_id] = handleAckTimer(3000,channel,state,timer_id,mqttcl,fake)

#if you have smart hub
def meross_hub_list():
  meross_post("/v1/Hub/getSubDevices")

def meross_post(url):
  global creds
  secret = "23x17ahWarFH6w29"
  extraData = {
	"email": email,
	"password" : password,
	"mobileInfo" : {
          "deviceModel": "armv7l",
          "mobileOsVersion": "#1488 SMP Thu Nov 18 16:15:28 GMT 2021",
          "mobileOs": "Linux",
          "uuid":  randomNonce(30,True) + uuid4(),
          "carrier":""
	}
  }
  params = ubinascii.b2a_base64(json.dumps(extraData).encode("utf8")).decode("utf8")
  nonce = randomNonce(16)
  timestamp = int(round(time.time() * 1000))
  signme = '%s%s%s%s' % (secret,timestamp,nonce,params)
  md5hash = md53.md5sum(signme.encode("utf8"))

  headers = {
    "AppVersion": "0.4.3.0",
    "Authorization": "Basic" if creds is None else "Basic %s" % creds["token"],
    "vender": "meross",
    "AppType": "MerossIOT",
    "AppLanguage": "EN",
    "User-Agent" : "MerossIOT/0.4.3.0"
  }
  payload = {
    'params': params,
    'sign': md5hash,
    'timestamp' : timestamp,
    'nonce'    : nonce
  }
  headers['Content-Type'] = 'application/x-www-form-urlencoded'
  r = urequests.post('https://iot.meross.com/' + url,headers=headers,data=urlencode(payload))
  print(r.status_code)
  try:
    resp = r.json()
  except:
    try:
     resp = r.text
    except:
      resp = r.content

  print(resp)
  return resp

#creates client_id and app_id
def generate_client_and_app_id():
  global app_id, client_id
  rnd_uuid = uuid4()
  app_id = md53.md5sum(f"API{rnd_uuid}".encode("utf8"))
  client_id = 'app:%s' % app_id

#requires user_id and key
#generates mqtt_pw
def generate_mqtt_password():
  global mqtt_pw
  clearpwd = f"{creds['user_id']}{creds['key']}"
  mqtt_pw = md53.md5sum(clearpwd.encode("utf8"))

#client-user-topic
#f"/app/{user_id}/subscribe"
#client-response-topic
#f"/app/{user_id}-{app_id}/subscribe"

#requires key, user_id, uuid
def meross_mqtt_build(channel,state,fake):
  nonce = randomNonce(16)
  messageId = md53.md5sum(nonce.encode("utf8")).lower()
  timestamp = int(round(time.time()))

  if not fake:
    strtohash = "%s%s%s" % (messageId, creds["key"], timestamp)
    signature = md53.md5sum(strtohash.encode("utf8")).lower()
  else:
    strtohash = "%s%s" % (messageId, timestamp)
    signature = md53.md5sum(strtohash.encode("utf8")).lower()
    
    creds = {
      'user_id' : "fakeid"
    }
    app_id = "fakeappid"
  data = {
    "header": {
      "from": f"/app/{creds['user_id']}-{app_id}/subscribe",
      "messageId": messageId,  # Example: "122e3e47835fefcd8aaf22d13ce21859"
      "method": "SET",  # Example: "GET",
      "namespace": "Appliance.Control.ToggleX",  # Example: "Appliance.System.All",
      "payloadVersion": 1,
      "sign": signature,  # Example: "b4236ac6fb399e70c3d61e98fcb68b74",
      "timestamp": timestamp,
      #"triggerSrc": "Android",
      #"uuid": uuid
    },
    "payload": {
      'togglex': {
        "onoff": 1 if state else 0,
        "channel": channel
      }
    }
  }

  strdata = json.dumps(data,separators=(',', ':')).encode("utf-8")
  print("sending")
  print(strdata)
  return strdata
"""
# 1. COMMANDS sent from the app to the device (/appliance/<uuid?>/subscribe) topic.
#    Such commands have "from" header populated with "/app/<userid>-<appuuid>/subscribe" as that tells the
#    device where to send its command ACK. Valid methods are GET/SET
# 2. COMMAND-ACKS, which are sent back from the device to the app requesting the command execution on the
#    "/app/<userid>-<appuuid>/subscribe" topic. Valid methods are GETACK/SETACK/ERROR
# 3. PUSH notifications, which are sent to the "/app/<userid>/subscribe" topic from the device (which populates
#    the from header with its topic /appliance/<uuid?>/subscribe). In this case, only the PUSH
#    method is allowed.
# Case 1 is not of our interest, as we don't want to get notified when the device receives the command.
# Instead we care about case 2 to acknowledge commands from devices and case 3, triggered when another app
# has successfully changed the state of some device on the network.
"""
