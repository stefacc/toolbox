# opensearch
https://www.youtube.com/watch?v=hPc1ecsxRBU
## send data to opensearch service
https://docs.aws.amazon.com/opensearch-service/latest/developerguide/gsgupload-data.html
```bash
# add one doc with index
curl -XPUT -u 'USERNAME:PASSWORD' 'ENDPOINT/INDEX/_doc/ID' -d '{"name": "Marco", "surname": "Rossi"}' -H 'Content-Type: application/json'

# add one doc with random index
curl -XPOST -u 'USERNAME:PASSWORD' 'ENDPOINT/INDEX/_doc' -d '{"name": "Claudia", "surname": "Rossi"}' -H 'Content-Type: application/json'

# using a bulk json file
curl -XPOST -u 'USERNAME:PASSWORD' 'ENDPOINT/_bulk' --data-binary @bulkcreate.json -H 'Content-Type: application/json'
curl -XPOST -u 'USERNAME:PASSWORD' 'ENDPOINT/_bulk' --data-binary @bulkupdate.json -H 'Content-Type: application/json'
```
bulkcreate.json
```json
{ "create": { "_index": "customer", "_id": "2" } }
{"name": "Valerio", "surname": "Rozzi"}
```
bulkupdate.json
```json
{ "update": { "_index": "customer", "_id": "2" } }
{"doc":{"name": "Valerio", "surname": "Rossi"}}
```
