# linux
## add full permission to folder and subfolder
```
sudo mkdir /var/directory
sudo chmod -R 777 /var/directory
```
## sed
[sed test website](https://sed.js.org/)
### replace one string only (in-file)
```
sed -i 's/FROM/TO/' file
```
### replace string A with string B, in-file *.txt named, excluding path C and path D in all sub-directories
```
find . -type f -name "*.txt" -not \( -path "./PATH_C/*" -prune \) -not \( -path "*/PATH_D*" -prune \) -exec sed -i 's/STRING_A/STRING_B/g' {} +
```
### remove all lines from string A to string B, in-file *.txt named, in all sub-directories in path C
```
find "PATH_C" -type f -name "*.txt" -exec sed -i '/STRING_A/,/STRING_B/d' {} +
```
