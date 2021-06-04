# Semes
Webservice for sending SMS using gammu as a daemon

## Installation instructions

### Debian Buster requirements
```
apt-get install python3-venv python3-dev libgammu-dev
mkdir /opt/semes
cd /opt/semes
python3.7 -m venv env37
. env37/bin/activate
pip install --upgrade pip setuptools
```

### Manually install python-gammu
```
cd /opt/semes
wget https://files.pythonhosted.org/packages/92/b5/9ac94f164fc3d72a5b92e9623ff986878a5f8e83b4e55362264f225677e4/python-gammu-3.1.tar.gz
tar -zxvf python-gammu-3.1.tar.gz
cd python-gammu-3.1
python ./setup.py install
```

### Install semes and all its requirements

```
cd /opt/semes
git clone https://github.com/nesiax/semes.git src
cd src
pip install -r requirements.txt
pip install -e .
```

### Run it.
Copy development.ini.example to development.ini and adjust your configuration

```
pserve --reload development.ini  
```

### See it in action

Point your browser to http://127.0.0.1:6543/semes/ (or similar)

<img src="https://github.com/nesiax/semes/blob/main/doc/images/send.png" width="360" height="760"/>
