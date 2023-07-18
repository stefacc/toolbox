### user-data to start vscode server at boot of an EC2
``` bash
#!/bin/bash
apt update
export HOME=/root
mkdir -p /root/.config/code-server
mkdir -p /root/.local/share/code-server/Machine
curl -fsSL https://code-server.dev/install.sh | sh
echo 'bind-addr: 0.0.0.0:8080
auth: none
password: PASSWORD
cert: false' > /root/.config/code-server/config.yaml
echo '{
    "terminal.integrated.defaultProfile.linux": "bash"
}' > /root/.local/share/code-server/Machine/settings.json 
systemctl enable --now code-server@root
```
