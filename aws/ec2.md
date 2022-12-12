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
[start-ec2.bat](start-ec2.bat) file to run this command on windows
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
[stop-ec2.bat](stop-ec2.bat) file to run this command on windows
## get all EC2 instances across all regions
```bash
for region in `aws ec2 describe-regions --region us-east-1 --output text | cut -f4`
do
     echo -e "\nListing Instances in region:'$region'..."
     aws ec2 describe-instances --region $region
done
```
