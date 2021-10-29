from smac_client import SMACClient
from smac_keys import smac_keys
import asyncio

CLIENTS = {}
CLIENT_INSTANCES = {}
TASKS = {}
TOTAL_VIRTUAL_DEVICES = 4

async def send_msg(client, id_device):
    c = 0
    await asyncio.sleep(1)
    print("sending msg", client, id_device)
    while c < 1000:
        print(id_device, c)
        client.send_message(frm=id_device, to="#", cmd=smac_keys["CMD_ONLINE"], message={})
        await  asyncio.sleep(.1)
        c += 1

def on_start(*args):
    print(args)

async def start():

    await asyncio.sleep(1)
    for dev in range(TOTAL_VIRTUAL_DEVICES):
        print("CLIENT{}".format(dev))
        CLIENTS[dev] = SMACClient()
        CLIENT_INSTANCES[dev] = asyncio.create_task( CLIENTS[dev].main() )
        TASKS[dev] = asyncio.create_task( send_msg(CLIENTS[dev], "D{}".format(dev)) )

    for i in CLIENT_INSTANCES.keys():
        await CLIENT_INSTANCES[i]
        await TASKS[i]

asyncio.run(start())