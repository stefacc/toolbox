from https://docs.aws.amazon.com/iot/latest/developerguide/register-CA-cert.html
## create custom-ca
### generate private key
```
openssl genrsa -out root_CA_key_filename.key 2048
```
### create CA certificate
```
openssl req -x509 -new -nodes -key root_CA_key_filename.key -sha256 -days 365 -out root_CA_cert_filename.pem
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
