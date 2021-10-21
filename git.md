# git
## cloning using custom path 
```
git clone **url-of-repo** directory
```
## moving  files or directories
also for submodules
```
git mv src dst
```
## adding submodule 
```
git submodule add **url-of-repo**
```
## cloning with submodules 
```
git clone --recurse-submodules **url-of-repo**
```
## moving repo git history to another repo 
```
cd repo-dest
git checkout master
git remote add repo-src **url-of-repo-src**
git fetch repo-src
git merge repo-src/master --allow-unrelated-histories
git remote rm repo-src (optional)
```
## aws credential-helper
- `.gitconfigure`
```
[credential "https://git-codecommit.eu-central-1.amazonaws.com/v1/repos/"]
helper = !aws codecommit credential-helper --profile myprofile $@
UseHttpPath = true
```
