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
## detach and remove volume
```bash
docker compose down --volumes
```
```bash
docker volume rm <VOLUME-NAME>
```
## stop and remove all containers
```bash
docker stop $(docker ps -a -q)
```
```bash
docker rm $(docker ps -aq)
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
## api
### run a container that can send request to the docker engine host
```bash
docker run -v /var/run/docker.sock:/var/run/docker.sock -it --rm alpine /bin/ash
```
### run a container that can send request to the docker engine host (using docker-compose)
```bash
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
environment:
  DOCKER_HOST: unix:///var/run/docker.sock
```
### example of request
```bash
curl --unix-socket /var/run/docker.sock -H "Content-Type: application/json" -d '{"Image": "alpine"}' -X POST http://localhost/v1.39/containers/create
```
## run a docker forever
```bash
CMD tail -f /dev/null
```
## aws-ecr to aws-ecr
```bash
aws ecr get-login-password --region <REGION> --profile <PROFILE> | docker login --username <USERNAME> --password-stdin <FROM-ECR-URL>

docker image pull <FROM-ECR-URL/IMAGE:TAG>
docker image tag <FROM-ECR-URL/IMAGE:TAG> <TO-ECR-URL/IMAGE:TAG>

aws ecr get-login-password --region <REGION> --profile <PROFILE> | docker login --username <USERNAME> --password-stdin <TO-ECR-URL>

docker image push <TO-ECR-URL/IMAGE:TAG>

docker image rm <FROM-ECR-URL/IMAGE:TAG>
docker image rm <TO-ECR-URL/IMAGE:TAG>
```
