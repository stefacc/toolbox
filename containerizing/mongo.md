# mongo
## mongo with replicas set
```bash
mongodb:
  image: mongo:7.0
  entrypoint: tail -f /dev/null
  # command: ["--replSet", "rs0", "--bind_ip_all", "--port", "27017"]
  extra_hosts:
    - "host.docker.internal:host-gateway"
  # environment:
    # - MONGO_INITDB_DATABASE=test
    # - MONGO_INITDB_ROOT_USERNAME=admin
    # - MONGO_INITDB_ROOT_PASSWORD=admin
  healthcheck:
    test: echo "try { rs.status() } catch (err) { rs.initiate({_id:'rs0',members:[{_id:0,host:'host.docker.internal:27017'}]}) }" | mongosh --port 27017 --quiet
    interval: 5s
    timeout: 30s
    start_period: 0s
    start_interval: 1s
    retries: 30
  volumes:
    - ./mongodb:/data/db
    - ./mongoconfig:/data/configdb
    # - ./mongo-entrypoint:/docker-entrypoint-initdb.d
  ports:
    - "27017:27017"
```
