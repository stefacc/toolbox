### user-data to start vscode server at boot of an EC2
aws ec2 get-console-output --instance-id ID --latest

``` bash
#!/bin/bash
PASSGEN=$(</dev/urandom tr -dc _A-Z-a-z-0-9 | head -c12)
apt update
export HOME=/root
mkdir -p /root/.config/code-server
mkdir -p /root/.local/share/code-server/Machine
curl -fsSL https://code-server.dev/install.sh | sh
echo 'bind-addr: 0.0.0.0:8080
auth: password
password: $PASSGEN
cert: false' > /root/.config/code-server/config.yaml
echo '{
    "terminal.integrated.defaultProfile.linux": "bash"
}' > /root/.local/share/code-server/Machine/settings.json 
systemctl enable --now code-server@root
echo "-----------------------------" >> /var/log/cloud-init-output.log 
echo $PASSGEN >> /var/log/cloud-init-output.log
echo "-----------------------------" >> /var/log/cloud-init-output.log
```
