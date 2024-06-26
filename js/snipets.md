# moment
## install module
```sh
npm install moment
```
## code
### convert local datetime string to utc object (DST auto-detect)
```js
var moment = require("moment");
datetime_utc = moment("2020-01-01 00:00:00").utc()
```
### utc object to string with custom format
```js
datetime_utc_str = datetime_utc.format('YYYY-MM-DD HH:mm:ss')
```
