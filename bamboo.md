# atlassian bamboo
## install
```bash
sudo apt install openjdk-8-jdk -y

mkdir bamboo-setup
wget https://www.atlassian.com/software/bamboo/downloads/binary/atlassian-bamboo-7.2.3.tar.gz
tar zxvf atlassian-bamboo-7.2.3.tar.gz -C bamboo-setup/
mkdir bamboo
nano bamboo-setup/atlassian-bamboo-7.2.3/atlassian-bamboo/WEB-INF/classes/bamboo-init.properties
=> bamboo.home=/home/ubuntu/bamboo
```
## run
```bash
cd bamboo-setup/atlassian-bamboo-7.2.3
./bin/start-bamboo.sh
```
