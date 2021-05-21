import os

PATH = "/home/manjunath/Desktop/SMAC_TEST"
SMAC_PATH = "/home/manjunath/Desktop/smac/smac_kivy"
VENV_PATH = "/home/manjunath/Desktop/smac/venv3.7_linux"
TOTAL_DEVICES = 10


os.system("mkdir {}".format(PATH))
for i in range(TOTAL_DEVICES):
    dev_path = "{}/DEVICE{}".format(PATH, i)
    print("Creating device at {}".format(dev_path))
    os.system("mkdir {}".format(dev_path))
    print('Copying files to {}'.format(dev_path))
    os.system("cp -r {}/* {}".format(SMAC_PATH, dev_path) )
    print("Running SMAC_INSTANCE at {}".format(dev_path))
    os.system("{}/bin/python {}/main.py &".format(VENV_PATH, dev_path) )
    print("\n\n")






