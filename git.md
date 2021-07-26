# git
## moving repo git history to another repo 
```
cd repo-dest
git checkout master
git remote add repo-src **url-of-repo-src**
git fetch repo-src
git merge repo-src/master --allow-unrelated-histories
git remote rm repo-src
```
## aws credential-helper
- `.gitconfigure`
```
[credential "https://git-codecommit.eu-central-1.amazonaws.com/v1/repos/"]
helper = !aws codecommit credential-helper --profile myprofile $@
UseHttpPath = true
```
