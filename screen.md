# screen
## open screen session
```bash
screen
```
## open screen session with name
```bash
screen -S NAME
```
## open screen session with name with command
```bash
screen -S NAME node app.js
```
## detach screen session
CTRL + A + D
## list screen sessions
```bash
screen -ls
```
## quit detached session
```bash
screen -X -S [session # you want to kill] quit
```
