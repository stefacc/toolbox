### configure sso profile
```bash
aws configure sso --profile PROFILE_NAME
```
### login sso profile
```bash
aws sso login --profile PROFILE_NAME
```
### add aws credentials helper
```bash
pip install git-remote-codecommit
```
### clone with sso profile
```bash
git clone codecommit::REGION://PROFILE_NAME@REPOSITORY
```
