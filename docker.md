# docker
## install
```bash
sudo su
apt update -y
curl -fsSL test.docker.com -o get-docker.sh && sh get-docker.sh
usermod -aG docker ubuntu

systemctl restart docker
```
## prune
- clean up any resources — images, containers, volumes, and networks
```bash
docker system prune
```
- clean up any resources — images, containers, volumes, and networks + stopped containers and all unused images
```bash
docker system prune -a
```
## remove image
- image
```bash
docker rmi Image1 Image2
```
- dangling image
```bash
docker image prune
```
- using a pattern
```bash
docker images -a | grep "pattern" | awk '{print $3}' | xargs docker rmi
```
- all
```bash
docker rmi $(docker images -a -q)
```
## create tar.gz from pulled images
```bash
docker save myhub/myimage | gzip > myimage.tar.gz
```
## load image from tar.gz
```bash
docker load -i myimage.tar.gz
```
## kill a container from inside (restart test)
```bash
kill -s SIGTERM 1
```
