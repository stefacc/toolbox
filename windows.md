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

## zip current folder with timestamp
`zipping.bat`: put it in a folder and run it, it creates `<folder name>-YYYYMMDDTHHMMSS.7z`
with everything inside (recursively), except the script itself.
Needs [7-Zip](https://www.7-zip.org/) with `7z` on PATH. The date parsing assumes the
`dd/mm/yyyy` short date format (e.g. Italian locale); for other formats adjust the
`%date:~...%` offsets.
```bat
@ECHO OFF
CLS

REM ISO 8601 Date and Time in basic format (YYYYMMDDTHHMMSS)
SET isodt=%date:~6,4%%date:~3,2%%date:~0,2%T%time:~0,2%%time:~3,2%%time:~6,2%
SET isodt=%isodt: =0%
ECHO ISO 8601 Date and Time in basic format (YYYYMMDDTHHMMSS): %isodt%

for %%I in (.) do set CurrDirName=%%~nxI
echo %CurrDirName%

7z a -r %CurrDirName%-%isodt% * -x!zipping.bat
```
