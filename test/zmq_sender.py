
from smac_device import client
import time
from smac_keys import smac_keys

counter = 0

while counter < 1001:
    #d = {}
    #d[smac_keys["FROM"]] = "D1"
    #d[smac_keys["TO"]] = "#"
    #d[smac_keys["CMD"]] = smac_keys["CMD_TEST"]
    #d[smac_keys["MESSAGE"]] = "Hello World"
    client.send_message(frm="D1", to="#", cmd=smac_keys["CMD_ONLINE"], message="Helloi world", udp=False, tcp=True)
    counter += 1
    print("msg counter", counter)
    time.sleep(.1)
