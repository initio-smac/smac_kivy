# smac_kivy
Kivy client for SMAC

python version = 3.7.4
kivy version = 2.0.0
buildozer version = 1.2.0

# installing python3.7
https://linuxize.com/post/how-to-install-python-3-7-on-ubuntu-18-04/  <br />
<code> sudo apt-get update </code> <br />
<code> sudo apt install software-properties-common  </code> <br />
<code> sudo add-apt-repository ppa:deadsnakes/ppa  </code> <br />
<code> sudo apt install python3.7  </code> <br />
</code>

# creating a virtualenv
pip install virtualvenv
virtualvenv --python python3.7 <venv_name>

# running the app
python main.py

# android build
buildozer android debug deploy run logcat

# repo
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
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

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

# buildozer android release
https://medium.com/modulotech/how-to-sign-an-unsigned-apk-using-command-line-636a056373a0
#1. Generate key
keytool -genkey -v -keystore smacapp.keystore -alias smacapp -keyalg RSA -keysize 2048 -validity 10000

prompts for the following
Password: Ssmrnk@61
Re-enter password: Ssmrnk@61
First Name and Last Name: Initio Energy
Name of the Organizational Unit: Smacsystem
Name of the Organization: Initio Energy Systems
City: Bengaluru
State: Karnataka
Country Code: IN

verify the data and generate keystore

#2. sign with jar signer
jarsigner -keystore <keystore_file>  -storepass <storepass> -keypass <keypass> <unsigned_apk_file> <alias_name>
jarsigner -keystore smacapp.keystore  -storepass Ssmrnk@6 -keypass Ssmrnk@6 smacapp-0.1-arm64-v8a-release-unsigned.apk smacapp


