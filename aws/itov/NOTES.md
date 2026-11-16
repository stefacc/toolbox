# itov — technical notes

## Prerequisites
- IAM user/role with permissions on CloudFormation, EC2, IAM, S3, SSM.
- CLI profile `itov`:
  ```powershell
  aws configure --profile itov     # region e.g. eu-west-3
  ```
- Session Manager plugin installed (needed for `connect` and `shell`).

## Choosing region and GPU
| Type | GPU | Notes |
|---|---|---|
| g6e.xlarge / 2xlarge | L40S 48 GB | faster; not offered in every EU region (e.g. missing in Milan, Ireland, London, Paris) |
| g6.2xlarge | L4 24 GB | cheap; Wan 2.2 14B fp8 runs by swapping between the two models |
| g5.2xlarge | A10G 24 GB | alternative to the L4 |

- On-demand GPUs can be sold out (`InsufficientInstanceCapacity`): try other AZs, other regions or other types.
- To check capacity quickly: `aws ec2 run-instances` on a specific AZ and `terminate-instances` right after
  (much faster than waiting for the CloudFormation rollback).
- The "Running On-Demand G and VT instances" quota is **per region** and can be 0: request an increase in Service Quotas
  (4 vCPUs for g6e.xlarge, 8 for g6e.2xlarge / g6.2xlarge).

## Indicative times and costs
- Setup on first boot: ~25 min (packages, ComfyUI, ~35 GB of models). Log: `/var/log/itov-setup.log`.
- 5 s clip, 832x480, 81 frames, 4-step LoRA on L4: ~5 min on the first run (~$0.10).
- On-demand: g6.2xlarge ~$1.2/h, g6e.xlarge ~$2/h, g6e.2xlarge ~$2.4/h (vary by region).
- 200 GB gp3 disk ≈ $18–19/month even with the instance stopped.

## Common issues
- **Antivirus/proxy with HTTPS inspection** → the CLI fails with `CERTIFICATE_VERIFY_FAILED`.
  Fix: exclude `*.amazonaws.com` and `*.aws.amazon.com` from inspection (otherwise the traffic is visible to the proxy).
- **Git Bash** rewrites arguments starting with `/` (e.g. SSM parameter names) → `export MSYS_NO_PATHCONV=1`.
- After installing the Session Manager plugin, consoles that were already open don't find it in the PATH
  (`itov.ps1` adds it automatically).
- A **tunnel left open** prevents the auto-shutdown: close it when you are done.
- The bucket has `DeletionPolicy: Retain`: `destroy` empties it and deletes it separately.

## Budget (optional, outside the stack)
Monthly AWS Budget with email alerts at 50/80/100% + forecast, and a `STOP_EC2_INSTANCES` budget action
on the instance id at 100% (IAM role with policy `AWSBudgetsActions_RolePolicyForResourceAdministrationWithSSM`).
It must be updated for every new instance and deleted by hand when everything is removed.
