# toolbox

## docker
- install
```
sudo su
apt update -y
curl -fsSL test.docker.com -o get-docker.sh && sh get-docker.sh
usermod -aG docker ubuntu

systemctl restart docker
```
### buildx
```
sudo su
apt install binfmt-support qemu-user-static
export DOCKER_CLI_EXPERIMENTAL=enabled
export DOCKER_BUILDKIT=1
docker build --platform=local -o . git://github.com/docker/buildx
mkdir -p ~/.docker/cli-plugins
mv buildx ~/.docker/cli-plugins/docker-buildx
```
