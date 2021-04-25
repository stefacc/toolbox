# git
## aws credential-helper
```
[credential "https://git-codecommit.eu-central-1.amazonaws.com/v1/repos/"]
helper = !aws codecommit credential-helper --profile myprofile $@
UseHttpPath = true
```
