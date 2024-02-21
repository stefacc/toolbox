# linux
## get name of current directory without full path
```
CURRENT_DIR=${$PWD##*/}
or
BASE=$(basename $PWD)
```
## add full permission to folder and subfolder
```
sudo mkdir /var/directory
sudo chmod -R 777 /var/directory
```
## find
### find all files with ``js`` suffix excluding path A
```
find -name "*.js" -not -path "./PATH_A/*"
```
## sed
[sed test website](https://sed.js.org/)
### replace one string only (in-file)
```
sed -i 's/FROM/TO/' file
```
### remove first char of string if char == CHAR, if CHAR == . remove first char
```
sed 's/^CHAR//'
```
### remove last char of string if char == CHAR, if CHAR == . remove last char
```
sed 's/CHAR$//'
```
### change \\" to ", useful when a json string is embedded in a json
```
sed 's/\\"/"/g'
```
### replace string A with string B, in-file *.txt named, excluding path C and path D in all sub-directories
```
find . -type f -name "*.txt" -not \( -path "./PATH_C/*" -prune \) -not \( -path "*/PATH_D*" -prune \) -exec sed -i 's/STRING_A/STRING_B/g' {} +
```
### remove all lines from string A to string B, in-file *.txt named, in all sub-directories in path C
```
find "PATH_C" -type f -name "*.txt" -exec sed -i '/STRING_A/,/STRING_B/d' {} +
```
## python & pip
### get version of libraries when using virtual enviroment
```
ls -d *.dist-info
```
## copy
### create link cp to copy
```
ln -s /bin/cp /bin/copy
```
