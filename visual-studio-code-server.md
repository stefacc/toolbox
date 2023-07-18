### user-data to start at boot of an EC2
``` bash
#!/bin/bash
apt update
export HOME=/root
mkdir -p /root/.config/code-server
curl -fsSL https://code-server.dev/install.sh | sh
echo 'bind-addr: 0.0.0.0:8080
auth: none
password: PASSWORD
cert: false' > /root/.config/code-server/config.yaml 
systemctl enable --now code-server@root
```