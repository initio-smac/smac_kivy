from smac_platform import SMAC_PLATFORM

def on_task_removed(*args):
    print("APP removed")
    print(args)

# service not restarted
# https://stackoverflow.com/questions/51357772/android-service-not-restarted-when-app-back-from-idle-state
from jnius import autoclass
PythonService = autoclass('org.kivy.android.PythonService')
PythonService.mService.setAutoRestartService(True)
#PythonService.mService.onTaskRemoved = on_task_removed
PythonService.mService.onDestroy = on_task_removed
print("SERVICE RESTART CODE RUN")

import time
import asyncio

async def start():
    await asyncio.sleep(1)
    while 1:
        print(time.time())
        await asyncio.sleep(1)

async def main():
    t1 = asyncio.create_task(start())
    await t1

asyncio.run(main())

