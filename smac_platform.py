SMAC_PLATFORM = None

try:
	import machine
	SMAC_PLATFORM = "ESP"
except:
	SMAC_PLATFORM = "KIVY"