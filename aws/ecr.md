# ecr
## list-images 
```bash
aws ecr list-images --repository-name <NAME> --profile <PROFILE>
```
result
```bash
{
    "imageIds": [
        {
            "imageDigest": "sha256:<SHA>",
            "imageTag": "<TAG>"
        }
    ]
}
```
## batch-delete-image
```bash
aws ecr batch-delete-image --repository-name <NAME> --image-ids imageTag=<TAG> --profile <PROFILE>
```
