FROM public.ecr.aws/docker/library/node:iron-bookworm

WORKDIR /app

COPY package.json package.json
RUN npm install

COPY source.js source.js
COPY destination.js destination.js
