# PM2
## install
```bash
sudo npm install -g pm2
```
## run nodejs app at startup
```bash
pm2 startup -u USER
cd APP-DIR
pm2 start app.js -n app-service
pm2 save
```
