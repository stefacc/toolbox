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
git submodule add **url-of-repo** <dst optional>
```
## cloning with submodules 
```
git clone --recurse-submodules **url-of-repo**
```
## deleting submodule
```
0. mv a/submodule a/submodule_tmp

1. git submodule deinit -f -- a/submodule    
2. rm -rf .git/modules/a/submodule
3. git rm -f a/submodule
# Note: a/submodule (no trailing slash)

# or, if you want to leave it in your working tree and have done step 0
3.   git rm --cached a/submodule
3bis mv a/submodule_tmp a/submodule
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
## duplicating or mirroring a repo 
```
git clone --bare https://github.com/EXAMPLE-USER/OLD-REPOSITORY.git
cd OLD-REPOSITORY.git
git push --mirror https://github.com/EXAMPLE-USER/NEW-REPOSITORY.git
cd ..
rm -rf OLD-REPOSITORY.git
```
## creating a new git master branch (or to remove history)
```
git checkout --orphan new-master
git rm -rf .
git branch -m master old-master
git branch -m new-master master
git push -f origin master
```
## aws credential-helper
- `.gitconfigure`
```
[credential "https://git-codecommit.eu-central-1.amazonaws.com/v1/repos/"]
helper = !aws codecommit credential-helper --profile myprofile $@
UseHttpPath = true
```
