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
