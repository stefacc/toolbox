FROM public.ecr.aws/docker/library/node:iron-bookworm

WORKDIR /app

COPY src/package.json package.json
RUN npm install

COPY src/index.js index.js

EXPOSE 8080
CMD ["node", "index.js"]
