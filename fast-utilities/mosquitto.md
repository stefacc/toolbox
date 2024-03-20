# mosquitto
## broker and bridge on ec2 (amazon linux 2)
```bash
#!/bin/bash

yum update -y
yum install python3 python3-pip unzip zip -y

pip3 install "paho-mqtt<2.0.0"

cd /home/ec2-user

yum groupinstall "Development Tools" -y
yum install make openssl-devel cmake -y

git clone https://github.com/DaveGamble/cJSON.git
cd cJSON && mkdir build && cd build
cmake ..
make
make install

cd /home/ec2-user

wget http://mosquitto.org/files/source/mosquitto-2.0.18.tar.gz
tar xvzf mosquitto-2.0.18.tar.gz
cd mosquitto-2.0.18/
make
make install

cd /home/ec2-user

rm -rf mosquitto-2.0.18
rm -rf cJSON

cat <<EOF> /etc/systemd/system/mosquitto.service
[Unit]
Description=Mosquitto MQTT Broker daemon
ConditionPathExists=/etc/mosquitto/mosquitto.conf
After=network.target
Requires=network.target

[Service] 
Type=forking 
User=mosquitto
RemainAfterExit=no 
StartLimitInterval=0 
ExecStart=/bin/sh -c "/usr/local/sbin/mosquitto -c /etc/mosquitto/mosquitto.conf -d -v"
ExecReload=/bin/kill -HUP $MAINPID 
Restart=on-failure 
RestartSec=2

[Install] 
WantedBy=multi-user.target
EOF

cat <<EOF> /etc/mosquitto/mosquitto.conf

connection iotcloudbridge
address localhost:8883
listener 1883 0.0.0.0

topic toIoTCloud/# out 0

bridge_protocol_version mqttv311
bridge_insecure true
persistence false
allow_anonymous true
cleansession false
clientid thingDevice-001
start_type automatic
notifications false
log_type all
try_private false
pid_file /var/run/mosquitto/mosquitto.pid
user mosquitto
bridge_cafile ca.pem
bridge_certfile cert.crt
bridge_keyfile private.key
EOF

adduser mosquitto
usermod -aG wheel mosquitto
/usr/bin/mkdir -m 740 -p /var/run/mosquitto
chown mosquitto:mosquitto /var/run/mosquitto

systemctl start mosquitto.service
```
