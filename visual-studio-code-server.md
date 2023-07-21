### user-data to start vscode server at boot of an EC2
``` bash
#!/bin/bash
PASSGEN=$(</dev/urandom tr -dc _A-Z-a-z-0-9 | head -c12)
HOSTEDZONE=$(aws route53 list-hosted-zones | jq -r ".HostedZones[0].Id")

yum update -y
yum install -y git
export HOME=/root
mkdir -p /root/.config/code-server
mkdir -p /root/.local/share/code-server/Machine
curl -fsSL https://code-server.dev/install.sh | sh
echo 'bind-addr: 0.0.0.0:8080
auth: password
password: PASSGEN
cert: false' > /root/.config/code-server/config.yaml

sed -i.bak s/PASSGEN/${PASSGEN}/g /root/.config/code-server/config.yaml

echo '{
    "terminal.integrated.defaultProfile.linux": "bash"
}' > /root/.local/share/code-server/Machine/settings.json 
systemctl enable --now code-server@root

echo "<<<----------------------------->>>"
cat /root/.config/code-server/config.yaml
echo "<<<----------------------------->>>"

TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
TARGETIP=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -v http://169.254.169.254/latest/meta-data/public-ipv4)

echo '{
  "Comment": "change request",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "DOMAIN",
        "Type": "A",
        "TTL": 360,
        "ResourceRecords": [
        {
            "Value": "TARGETIP"
          }
        ]
      }
    }
  ]
}' > change-resource-record-sets.json

sed -i.bak s/TARGETIP/${TARGETIP}/g change-resource-record-sets.json
aws route53 change-resource-record-sets --hosted-zone-id $HOSTEDZONE --change-batch file://change-resource-record-sets.json
```
### show log from ec2 to get vs-code-server password (using cloudshell)
``` bash
aws ec2 get-console-output --instance-id ID --latest
```
