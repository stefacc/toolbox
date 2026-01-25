# windows
## rename all files with prefix
in powershell
```
$items=Get-ChildItem;
$items | Rename-Item -NewName { "Prefix_" + $_.Name };
```
## volume C extension
[youtube link](https://www.youtube.com/watch?v=9C2Frs3DRPI)
## windows 11
### how to clean C: unit
open ``Run`` and launch ``cleanmgr/low disk``
### terminal log saver
```
$ErrorActionPreference="SilentlyContinue"
Stop-Transcript | out-null
$ErrorActionPreference = "Continue"
Start-Transcript -path C:\output.txt -append
# Do some stuff
Stop-Transcript
```
