# itov — Private image-to-video on AWS

Turns images into short videos (~5 s clips) with **ComfyUI + Wan 2.2 I2V 14B** on an NVIDIA GPU
in **your own** AWS account. Images never leave the account: no external services, no open ports.

```
aws/itov/
├── itov.ps1            control script (deploy, start, connect, stop, ...)
├── infra/itov.yaml     CloudFormation: GPU, encrypted disk and bucket, SSM-only access
├── tools/itov_test.py  end-to-end test with a synthetic image
└── NOTES.md            GPUs/regions, quotas, costs, common issues
```

## Requirements
- **Windows** with PowerShell (the script is `.ps1`).
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and an IAM user with permissions on
  CloudFormation, EC2, IAM, S3 and SSM.
- [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)
  for the AWS CLI.
- GPU quota in the chosen region (see step 2).

## Quick start (from scratch)

### 1. Clone and configure credentials
```powershell
git clone https://github.com/stefacc/toolbox.git
cd toolbox\aws\itov
aws configure --profile itov          # access key, secret key, region (e.g. eu-west-3)
aws sts get-caller-identity --profile itov   # must answer with your account
```
If Windows blocks scripts, use this form for all the commands below:
`powershell -ExecutionPolicy Bypass -File .\itov.ps1 <command>`
or, once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### 2. Choose region and GPU (and check the quota)
Default: region **eu-west-3** (Paris) with **g6.2xlarge** (NVIDIA L4 24 GB, ~$1.2/h).
To change them, before deploying:
```powershell
$env:ITOV_REGION = "eu-north-1"     # e.g. Stockholm
$env:ITOV_TYPE   = "g6e.xlarge"     # L40S 48 GB, faster (~$2/h), not available in every region
```
The region's **"Running On-Demand G and VT instances"** quota must be ≥ the machine's vCPUs
(8 for g6.2xlarge). Check it:
```powershell
aws service-quotas get-service-quota --service-code ec2 --quota-code L-DB2E81BA --profile itov --region eu-west-3
```
If it is 0, request an increase from the *Service Quotas* console (approval takes from a few hours to a day).

### 3. Deploy
```powershell
.\itov.ps1 deploy               # optional: .\itov.ps1 deploy eu-west-3a  (specific availability zone)
```
If it fails with *insufficient capacity*, the GPU is sold out in that zone: retry with another AZ, region or type
(first run `aws cloudformation delete-stack --stack-name itov --profile itov --region <region>`).

### 4. Wait for the setup (~25 min, first time only)
```powershell
.\itov.ps1 status               # "SETUP: in progress" → "SETUP: done"
```
The instance installs ComfyUI and downloads ~35 GB of models.

### 5. (Optional) Test
```powershell
.\itov.ps1 test                 # generates a test clip (~5 min on L4)
.\itov.ps1 download .\output    # downloads the generated videos
```

### 6. Use ComfyUI
```powershell
.\itov.ps1 connect              # opens http://localhost:8188 — keep the window open (it is the tunnel)
```
In ComfyUI: **Workflow → Browse Templates → Video → "Wan 2.2 14B Image to Video"**, load the image in the
*Load Image* node, describe the motion in the prompt and press **Run**. The template with the 4-step lightx2v LoRA is much faster.

### 7. When you are done
```powershell
.\itov.ps1 stop                 # shuts down (it also shuts down by itself after 30 min idle with the tunnel closed)
.\itov.ps1 destroy              # deletes EVERYTHING: instance, disk with models, bucket
```

## All commands
| Command | What it does |
|---|---|
| `deploy [az]` | creates/updates the infrastructure |
| `start` / `stop` | starts / stops the instance (the disk is kept) |
| `status` | instance state and setup progress |
| `connect` | SSM tunnel + opens ComfyUI on `localhost:8188` |
| `upload <folder>` | uploads images to ComfyUI/input (via encrypted S3) |
| `download <folder>` | downloads the generated videos |
| `wipe` | deletes input/output from instance and bucket |
| `test` | test clip with a synthetic image |
| `shell` | shell on the instance (via SSM) |
| `destroy` | deletes everything |

## Security
- Instance with **no inbound ports**: access only through AWS SSM (encrypted tunnel, IAM-authenticated).
- ComfyUI listens only on the instance's `127.0.0.1`; "API" nodes (external cloud services) are disabled.
- **Encrypted** EBS disk and S3 bucket; bucket with Block Public Access and HTTPS only.
- Outbound internet is needed only for the setup (packages and model weights from Hugging Face).
- If an antivirus/proxy inspects HTTPS, exclude `*.amazonaws.com` and `*.aws.amazon.com`: otherwise the CLI fails
  and the proxy would see the traffic.

## Indicative costs
- GPU running: g6.2xlarge ~$1.2/h · g6e.xlarge ~$2/h. Stopped: $0 compute.
- 200 GB disk: ~$18/month **even with the instance stopped** → `destroy` when no longer needed.
- An AWS Budget with email alerts is recommended (see [NOTES.md](NOTES.md)).
