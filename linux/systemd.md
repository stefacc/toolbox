# how to create a systemd service in linux
[link](https://www.shubhamdipt.com/blog/how-to-create-a-systemd-service-in-linux/)
## steps
- ``cd /etc/systemd/system``
- ``nano my-service.service``
```
[Unit]
Description=<description about this service>

[Service]
User=<user e.g. root>
WorkingDirectory=<directory_of_script e.g. /root>
ExecStart=<script which needs to be executed>
# optional items below
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
- reload daemon engine: ``sudo systemctl daemon-reload``
- start service: ``sudo systemctl start my-service.service``
- get service status: ``sudo systemctl status my-service.service``
- enable service to run on every reboot: ``sudo systemctl enable my-service.service``
- disable service on every reboot: ``sudo systemctl disable my-service.service``
