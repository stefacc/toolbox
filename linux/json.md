# json
## website to format and validate json string (likes ' -> ")
[https://jsonformatter.curiousconcept.com/](https://jsonformatter.curiousconcept.com/)
## jq
[https://www.devtoolsdaily.com/jq_playground/](https://www.devtoolsdaily.com/jq_playground/)

jq example with json file input
```json
{
   "timestamp":"XXXXXX",
   "services":[
      {
         "service":"A-ingestion",
         "ip":"192.168.1.1"
      },
      {
         "service":"B-db",
         "ip":"192.168.1.2"
      }
   ]
}
```
```bash
WRAPPER=$(cat /file.json | jq '.services[]  | select(.name | endswith("-db"))  | .ip')
echo $WRAPPER

192.168.1.2
```
### add object to services array
```bash
jq --argjson service "C-rest-api-server" --arg ip "192.168.1.3" '.services += [{service: $service, ip: $ip, ports:[]}]' config.json > config.json.tmp 

--arg: to add "formatted" element
--argjson: to add "no-json-formatted" element, example: "true" => true (json-like)

config.json is the input file and it can not be overwrite
solution:
mv config.json.tmp config.json
```
### add object to array in a specific element
try to add port in "ports" array of service named "C-rest-api-server"
```bash
jq --arg service "C-rest-api-server" --arg port 8080 '.services |= map(select(.service="$service").ports |= . + [$port])' config.json > config.json.tmp
mv config.json.tmp config.json
jq --arg service "C-rest-api-server" --arg port 8088 '.services |= map(select(.service="$service").ports |= . + [$port])' config.json > config.json.tmp
mv config.json.tmp config.json
```
