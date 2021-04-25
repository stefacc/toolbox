# toolbox

## docker
- install
```bash
sudo su
apt update -y
curl -fsSL test.docker.com -o get-docker.sh && sh get-docker.sh
usermod -aG docker ubuntu

systemctl restart docker
```
### buildx
- install
```bash
sudo su
apt install binfmt-support qemu-user-static

export DOCKER_CLI_EXPERIMENTAL=enabled
export DOCKER_BUILDKIT=1
docker build --platform=local -o . git://github.com/docker/buildx

mkdir -p ~/.docker/cli-plugins
mv buildx ~/.docker/cli-plugins/docker-buildx
```
- builder creation using a random name
```bash
docker run --rm --privileged docker/binfmt:820fdd95a9972a5308930a2bdfb8573dd4447ad3

docker buildx create --use
docker buildx inspect --bootstrap
```
- builder creation using a custom name
```bash
docker run --rm --privileged docker/binfmt:820fdd95a9972a5308930a2bdfb8573dd4447ad3

docker buildx create --name mybuilder
docker buildx use mybuilder
docker buildx inspect --bootstrap
```
- supported platform
``` 
Platforms: linux/amd64, linux/arm64, linux/ppc64le, linux/s390x, linux/386, linux/arm/v7, linux/arm/v6
``` 
