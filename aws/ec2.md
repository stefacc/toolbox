# ec2
## start an ec2 machine
```bash
aws ec2 start-instances --instance-ids <ID>
```
result
```bash
{
    "StartingInstances": [
        {
            "CurrentState": {
                "Code": 0,
                "Name": "pending"
            },
            "InstanceId": "<ID>",
            "PreviousState": {
                "Code": 80,
                "Name": "stopped"
            }
        }
    ]
}
```
### file
``.bat`` file to run this command on windows
## stop an ec2 machine
```bash
aws ec2 stop-instances --instance-ids <ID>
```
result
```bash
{
    "StoppingInstances": [
        {
            "CurrentState": {
                "Code": 64,
                "Name": "stopping"
            },
            "InstanceId": "<ID>",
            "PreviousState": {
                "Code": 16,
                "Name": "running"
            }
        }
    ]
}
```
### file
``.bat`` file to run this command on windows
