# GreenGrass
## start an ec2 machine with Amazon Linux 2
```bash
#!/bin/bash

yum update -y
yum install java-1.8.0-amazon-corretto unzip -y

cd /home/ec2-user
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && sudo ./aws/install

sed -in 's/root\tALL=(ALL)/root\tALL=(ALL:ALL)/' /etc/sudoers

curl -s https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-nucleus-latest.zip > greengrass-nucleus-latest.zip && unzip greengrass-nucleus-latest.zip -d GreengrassCore && rm greengrass-nucleus-latest.zip

export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXXXXX
export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXX

java -Droot="/greengrass/v2" -Dlog.store=FILE -jar ./GreengrassCore/lib/Greengrass.jar --aws-region us-east-1 --thing-name thingDevice-001 --component-default-user ggc_user:ggc_group --provision true --setup-system-service true --deploy-dev-tools true

# sudo /greengrass/v2/alts/current/distro/bin/loader
```
