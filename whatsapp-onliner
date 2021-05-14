# whatsapp-onliner
add this script as a bookmark, one click on it after opening the victim's page

online/offline activity will be recorded on the chrome console
```
javascript: (function () { var j = 0, i = 0; setInterval(() => { var x = document.getElementsByTagName('span'); for (i = 0; i < x.length; i++) { if (x[i].title == 'online') { if (j == 0) { console.log(new Date().toISOString(), x[i].title); j = 1; break; } else break; } } if (i == x.length) { if (j == 1) console.log(new Date().toISOString(), 'offline'); j = 0; } }, 5000); })();
```
