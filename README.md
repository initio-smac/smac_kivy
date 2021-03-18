# smac_kivy
Kivy client for SMAC

python version = 3.7.4
kivy version = 2.0.0
buildozer version = 1.2.0

# installing python3.7
https://linuxize.com/post/how-to-install-python-3-7-on-ubuntu-18-04/ <br />
<code>
sudo apt-get update <br />
sudo apt install software-properties-common <br />
sudo add-apt-repository ppa:deadsnakes/ppa <br />
sudo apt install python3.7 <br />
</code>

# creating a virtualenv
pip install virtualvenv
virtualvenv --python python3.7 <venv_name>

# running the app
python main.py

# android build
buildozer android debug deploy run logcat

