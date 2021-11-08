
from smac_client import SMACClient
import time
import asyncio
from smac_keys import smac_keys


client = SMACClient()

async def send():
    counter = 0
    while counter < 1001:
        #d = {}
        #d[smac_keys["FROM"]] = "D1"
        #d[smac_keys["TO"]] = "#"
        #d[smac_keys["CMD"]] = smac_keys["CMD_TEST"]
        #d[smac_keys["MESSAGE"]] = "Hello World"
        client.send_message(frm="D1", to="#", cmd=smac_keys["CMD_ONLINE"], udp=False, tcp=True)
        counter += 1
        print("msg counter", counter)
        await asyncio.sleep(.01)

async def start():
    t1 = asyncio.create_task(client.main())
    t2 = asyncio.create_task(send())
    await t1
    await t2

asyncio.run(start())
