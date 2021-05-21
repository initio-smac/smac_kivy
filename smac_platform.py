from kivy import platform
import json
import random

TEST_DEVICE = True
SMAC_PLATFORM = None

# platform options
# android, ESP, RPI, win, linux

if TEST_DEVICE:
	TEST_PLATFORMS = ["android", "win", "linux", "ESP"]
	try:
		with open('config.json', 'r') as f:
			fd = json.load(f)
			if fd.get("PLATFORM", None) != None:
				SMAC_PLATFORM = fd.get("PLATFORM")
			else:
				SMAC_PLATFORM = random.choice(TEST_PLATFORMS)
				fd["PLATFORM"] = SMAC_PLATFORM
			f.close()

		with open('config.json', 'w') as f:
			f.write( json.dumps(fd) )
			f.close()
	except Exception as e:
		print("Test Device Platform Set error", e)
else:
	try:
		import machine
		SMAC_PLATFORM = "ESP"
	except:
		SMAC_PLATFORM = platform