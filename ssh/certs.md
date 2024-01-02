## Certificate Key Matcher
https://www.sslshopper.com/certificate-key-matcher.html
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
## ssh-ca
from https://www.lorier.net/docs/ssh-ca.html
```
Using a CA with SSH
Using a CA with ssh means you can sign a key for a user, and everywhere that the user trusts the CA you can login, without having to copy your SSH key everywhere again. This allows for things like fast rollover of keys (eg: daily), or trusting the fingerprint of a machine that you're logging into, which can be very useful when you're managing large numbers of machines, or machines that get new host keys (eg by reinstalling) regularly.

You'll probably want at least openssh 5.6, although some of the functionality is available in 5.3.

Creating the CA key
ssh-keygen -f /etc/ssh/ca
Signing your host keys
The -V flag specifies the validity interval. These will work from 5 minutes ago (to allow for clock drift), for another 10 years. Tweak as you see necessary.

the -h flag specifies what hostnames that this machine is allowed to assert. You might want to add other useful hostnames there.

ssh-keygen -s /etc/ssh/ca \
     -I "$(hostname --fqdn) host key" \
     -n "$(hostname),$(hostname --fqdn),$(hostname -I|tr ' ' ',')" \
     -V -5m:+3650d \
     -h \
     /etc/ssh/ssh_host_rsa_key.pub \
     /etc/ssh/ssh_host_dsa_key.pub \
     /etc/ssh/ssh_host_ecdsa_key.pub
Using the CA for host verification
The * below specifies that this is certificate authority is allowed to attest for any hostname, if you have one, or more common domain name suffixes, you might want to use (for example) *.example.org,*.example.net instead. Note that if you do replace the * in the known_hosts files with a domain name, they annoyingly won't match if you're using a DNS search path.

On the server that's being authenticated: for i in /etc/ssh/ssh_host*_key-cert.pub; do echo "HostCertificate $i" >>/etc/ssh/sshd_config done

System wide: echo "@cert-authority * $(cat /etc/ssh/ca.pub)" >>/etc/ssh/ssh_known_hosts

Per user: echo "@cert-authority * $(cat /etc/ssh/ca.pub)" >>~/.ssh/known_hosts

Signing your user keys
You might also want to change the validity, for example if you're rotating keys daily, you might want to set the validity to 24h instead of 10 years. The -n parameter specifies the name of the principals to assert, multiple can be listed comma seperated. The -O parameter (not shown) can be used to further restrict what the key can be used for. In particular you might want to set -O source-address=$(hostname -I | tr ' ' ',') so that the key can only be used from the set of IPs that the host has.

If you're using pkcs11 tokens to hold your ssh key, you may need to run ssh-keygen -D $PKCS11_MODULE_PATH >~/.ssh/id_rsa.pub so that you have a public key to sign. If your CA private key is being held in a pkcs11 token, you can use the -D parameter, in this case the -s parameter has to point to the public key of the CA.

ssh-keygen -s /etc/ssh/ca \
    -I "$(whoami)@$(hostname --fqdn) user key" \
    -n "$(whoami)" \
    -V -5m:+3650d \
    ~/.ssh/id_rsa.pub \
    ~/.ssh/id_dsa.pub \
    ~/.ssh/id_ecdsa.pub

ssh-add ~/.ssh/*-cert.pub
Using the CA for user verification
If you omit the AuthorizedPrincipalsFile option, and/or the principals= argument below, then the principal name must match the user they're trying to login as.

System wide:
echo "AuthorizedPrincipalsFile %h/.ssh/authorized_principals" >>/etc/ssh/sshd_config
echo "TrustedUserCAKeys /etc/ssh/ca.pub" >>/etc/ssh/sshd_config
echo $(whoami) > ~/.ssh/authorized_principals

Per user: echo "cert-authority,principals=$(whoami) $(cat /etc/ssh/ca.pub)" >>~/.ssh/authorized_keys

To revoke keys
Interestingly, the ssh CRL appears to not be signed, so anyone can create a new CRL, so make sure your CRLs are protected.

System wide:
echo "RevokedKeys /etc/ssh/revoked_keys" >>/etc/ssh/sshd_config
ssh-keygen -k -f /etc/ssh/revoked_keys $public_key_to_revoke
ssh-keygen -k -u -f /etc/ssh/revoked_keys $additional_public_keys_to_revoke
or:
echo "RevokedKeys /etc/ssh/revoked_keys" >>/etc/ssh/sshd_config
echo @revoked $(cat $public_key_to_revoke) >> /etc/ssh/revoked_keys

Per user: echo @revoked $(cat $public_key_to_revoke) >>~/.ssh/known_hosts

To use
If you specify the ssh key, then ssh will load the associated certificate. You can't add a certificate without the associated key.

For example, you can use ssh -i ~/.ssh/id_dsa $hostname (if the key is one of the default files, then you don't need to specify it.)

You can also load both the key and the certificate into an agent with the command ssh-add -i ~/.ssh/id_dsa.

Or, you can specify the command with .ssh/config file:

Host *.example.com
   IdentifyFile ~/.ssh/id_dsa
Hints
principals can be any strings, although usually are usernames, this can be used to provide "realms", for example by using "username@domain" as a principal, or "realm:username" or similar.
Gotchas
This is a generic ssh gotcha: Host clauses in ssh config match what you say on the command line. So Host *.example.org will only match if you type foo.example.org, but not foo. You possibly want to use: Match canonical *.example.org
```
