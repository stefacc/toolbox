best website [https://docs.aws.amazon.com/iot/latest/developerguide/register-CA-cert.html](https://dmuth.medium.com/ssh-at-scale-cas-and-principals-b27edca3a5d)
### create CA
```
ssh-keygen -t ecdsa -C "The CA" -N "" -f ca



ca
<private key - never share or commit it>

ca.pub
ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBM3yuU15oTcndIoOjPRWXf8I1VZvTLIzHJedG5DYJSoF5IHd2EU8K66gwS7YeCP
```
### create Key
```
ssh-keygen -t ecdsa or rsa -C "My Key" -N "" -f my-key



my-key
<private key - never share or commit it>

my-key.pub
ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBHnIl3GTDBLYtUsMTA1LTcr6cqtSGVn7/6H4li/nvElVIs1CdLlMZuTCM/x9hpj
```
## create certificates with custom-ca
### generate private key
```
openssl genrsa -out verification_cert_key_filename.key 2048
```
### create Certificate Signing Request
```
openssl req -new -key verification_cert_key_filename.key -out verification_cert_csr_filename.csr
```
### create a private key verification certificate
```
openssl x509 -req -in verification_cert_csr_filename.csr -CA root_CA_cert_filename.pem -CAkey root_CA_key_filename.key -CAcreateserial -out verification_cert_filename.pem -days 365 -sha256
```
