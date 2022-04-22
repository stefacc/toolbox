## files (certs and more)
- host_prv_key (server prv key)
- host_cert.pub (server certificate)
- user_ca_keys.pub (user CA pub Key)
- principals (authorized users file)
## sshd_config configuration
```
# Logging
SyslogFacility AUTH
LogLevel QUIET | FATAL | ERROR | INFO | VERBOSE | DEBUG | DEBUG1 | DEBUG2 | DEBUG3

# Auth
PermitRootLogin yes
PubkeyAuthentication yes
PasswordAuthentication yes
ChallengeResponseAuthentication no
UsePAM yes
 
# Keys
HostKey /path/host_prv_key
HostCertificate /path/host_cert.pub
TrustedUserCAKeys /path/user_ca_keys.pub
AuthorizedPrincipalsFile /path/principals
```
remember to restart the service
```
sudo systemctl restart sshd.service
```
