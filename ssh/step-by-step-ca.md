best website [https://docs.aws.amazon.com/iot/latest/developerguide/register-CA-cert.html](https://dmuth.medium.com/ssh-at-scale-cas-and-principals-b27edca3a5d)
### create CA
```
ssh-keygen -t ecdsa -C "The CA" -N "" -f ca



ca
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIJdesj80NvVAoGkPXTfSejJbf4816G7ojgK3VezgB0G8oAoGCCqGSM49
AwEHoUQDQgAEzfK5TXmhNyd0ig6M9FZd/wjVVm9MsjMcl50bkNglKgXkgd3YRTwr
rqDBLth4I9Qn5GcHb94lDtEyDw08R1JiHg==
-----END EC PRIVATE KEY-----

ca.pub
ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBM3yuU15oTcndIoOjPRWXf8I1VZvTLIzHJedG5DYJSoF5IHd2EU8K66gwS7YeCP
```
### create Key
```
ssh-keygen -t ecdsa or rsa -C "My Key" -N "" -f my-key



my-key
----BEGIN EC PRIVATE KEY-----
MHcCAQEEIMAfydf9anKzY0/wqTauXXpM6cJAj6RcWf5aCs7At0dHoAoGCCqGSM49
AwEHoUQDQgAEeciXcZMMEti1SwxMDUtNyvpyq1IZWfv/ofiWL+e8SVUizUJ0uUxm
5MIz/H2GmOu2aau7lKgN6mUq99KKMrG0VA==
-----END EC PRIVATE KEY-----

my-key.pub
ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBHnIl3GTDBLYtUsMTA1LTcr6cqtSGVn7/6H4li/nvElVIs1CdLlMZuTCM/x9hpj
```
### sign my-key.pub using CA
```
ssh-keygen -s ./ca -I testing-my-ca -n user1,user2 -V +1w -z 1 ./my-key.pub



my-key-cert.pub
ecdsa-sha2-nistp256-cert-v01@openssh.com AAAAKGVjZHNhLXNoYTItbmlzdHAyNTYtY2VydC12MDFAb3BlbnNzaC5jb20AAAAgpAURhTf5sRC6x1A+zHXZX/26hZXjYY
```
### info about cert
```
ssh-keygen -L -f ./my-key-cert.pub



./my-key-cert.pub:
Type: ecdsa-sha2-nistp256-cert-v01@openssh.com user certificate
Public key: ECDSA-CERT SHA256:reZYAy81/1QPDvgAC9ktZ2fJd9P3ZbvkHQfiFj1t5zg
Signing CA: ECDSA SHA256:DldnVFM/w4+C2mingaOzF2yqoHpSZDrAs90PZBET2tc
Key ID: "testing-my-ca"
Serial: 1
Valid: from 2021-03-11T10:00:00 to 2021-03-18T10:01:30
Principals:
user1
user2
Critical Options: (none)
Extensions:
permit-X11-forwarding
permit-agent-forwarding
permit-port-forwarding
permit-pty
permit-user-rc
```
### set sshd_config
```
HostKey /etc/ssh/my-key
HostCertificate /etc/ssh/my-key-cert.pub
TrustedUserCAKeys /etc/ssh/ca.pub
AuthorizedPrincipalsFile /etc/ssh/auth_principals/%u

con two text files in /etc/ssh/auth_principals/*
- ./user1
-- user1
-- user2
- ./user2
-- user2
```
