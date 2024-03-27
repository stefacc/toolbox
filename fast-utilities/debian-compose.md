# debian container to run with compose
## folder tree
![alt text](https://github.com/stefacc/toolbox/blob/main/fast-utilities/tree.jpg?raw=true)
## src/start.sh
```bash
#!/bin/bash

figlet $TITLE
echo $(date)

DOCKERINFO=$(curl -s --unix-socket /run/docker.sock http://docker/containers/$HOSTNAME/json | jq '.Name' )
DOCKERINFO_CLEANED=$(sed -e 's/^"//' -e 's/"$//' -e 's/\///g' <<<"$DOCKERINFO")
echo "name: $DOCKERINFO_CLEANED"
```
## build_and_run.sh
```bash
#!/bin/bash
# docker build . -t base
docker compose up --build
```
## docker-compose.yml
```bash
#!/bin/bash
services:
  app:
    image: base
    build:
      dockerfile: Dockerfile
    entrypoint: /src/start.sh
    volumes:
      - ./storage:/storage
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - TITLE=APP CONTAINER
      - DOCKER_HOST=unix:///run/docker.sock
```
## Dockerfile
```
FROM public.ecr.aws/debian/debian:bullseye-slim as builder
WORKDIR /

RUN apt update -y
RUN apt install curl figlet jq sed -y

COPY ./src /src
RUN chmod +x /src/start.sh

ENTRYPOINT ["/bin/bash", "/src/start.sh"]
```
