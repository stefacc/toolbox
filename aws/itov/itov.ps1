<#
  itov - control the AWS GPU running ComfyUI + Wan 2.2

  .\itov.ps1 deploy          creates/updates the infrastructure (once)
  .\itov.ps1 start           starts the instance
  .\itov.ps1 connect         opens the tunnel and ComfyUI on http://localhost:8188
  .\itov.ps1 stop            stops the instance (it also stops by itself after 30 min idle)
  .\itov.ps1 status          instance state + setup
  .\itov.ps1 upload <dir>    uploads the images in a folder to ComfyUI/input (via encrypted S3)
  .\itov.ps1 download <dir>  downloads the generated videos to a local folder
  .\itov.ps1 wipe            deletes input/output on the instance AND the bucket
  .\itov.ps1 shell           shell on the instance (via SSM)
  .\itov.ps1 test            generates a test clip from a synthetic image
  .\itov.ps1 destroy         deletes EVERYTHING (instance, disk, bucket)
#>
param(
  [Parameter(Position = 0)][string]$Cmd = "status",
  [Parameter(Position = 1)][string]$Arg
)
$ErrorActionPreference = "Stop"

$Profile_ = "itov"
$Region   = if ($env:ITOV_REGION) { $env:ITOV_REGION } else { "eu-west-3" }
$Stack    = "itov"
$Type     = if ($env:ITOV_TYPE) { $env:ITOV_TYPE } else { "g6.2xlarge" }
$Root     = $PSScriptRoot
$Common   = @("--profile", $Profile_, "--region", $Region)
$Smp = "C:\Program Files\Amazon\SessionManagerPlugin\bin"
if ((Test-Path $Smp) -and ($env:Path -notlike "*SessionManagerPlugin*")) { $env:Path += ";$Smp" }

function Aws { & aws.exe @args @Common; if ($LASTEXITCODE -ne 0) { throw "aws $($args[0..1] -join ' ') failed" } }

function Out-Stack($key) {
  Aws cloudformation describe-stacks --stack-name $Stack `
    --query "Stacks[0].Outputs[?OutputKey=='$key'].OutputValue" --output text
}

function Get-Ids {
  $script:Iid    = Out-Stack "InstanceId"
  $script:Bucket = Out-Stack "BucketName"
}

function Wait-Running {
  Write-Host "Waiting for the instance to be ready for SSM..."
  Aws ec2 wait instance-running --instance-ids $Iid
  for ($i = 0; $i -lt 60; $i++) {
    $s = Aws ssm describe-instance-information --filters "Key=InstanceIds,Values=$Iid" `
      --query "InstanceInformationList[0].PingStatus" --output text
    if ($s -eq "Online") { return }
    Start-Sleep 5
  }
  throw "The SSM agent is not responding"
}

function Invoke-Remote([string]$Command) {
  $tmp = New-TemporaryFile
  @{ commands = @($Command) } | ConvertTo-Json -Compress | Set-Content $tmp -Encoding ascii
  $cid = Aws ssm send-command --instance-ids $Iid --document-name AWS-RunShellScript `
    --parameters "file://$tmp" --query "Command.CommandId" --output text
  Remove-Item $tmp
  do {
    Start-Sleep 3
    $st = & aws.exe ssm get-command-invocation --command-id $cid --instance-id $Iid @Common `
      --query Status --output text 2>$null
  } while ($st -in @("Pending", "InProgress", "Delayed", ""))
  Aws ssm get-command-invocation --command-id $cid --instance-id $Iid `
    --query "[StandardOutputContent,StandardErrorContent]" --output text
  if ($st -ne "Success") { throw "Remote command: $st" }
}

switch ($Cmd) {
  "deploy" {
    Aws cloudformation deploy --template-file "$Root\infra\itov.yaml" --stack-name $Stack `
      --capabilities CAPABILITY_IAM --no-fail-on-empty-changeset `
      --parameter-overrides "AvailabilityZone=$Arg" "InstanceType=$Type"
    Get-Ids
    Write-Host "Instance: $Iid  Bucket: $Bucket"
    Write-Host "The first setup (ComfyUI + ~35GB of models) takes ~20-30 min. Check with: .\itov.ps1 status"
  }
  "start" {
    Get-Ids; Aws ec2 start-instances --instance-ids $Iid | Out-Null; Wait-Running
    Write-Host "Running. Next: .\itov.ps1 connect"
  }
  "stop" {
    Get-Ids; Aws ec2 stop-instances --instance-ids $Iid | Out-Null
    Write-Host "Stopping (the disk with models and work is kept)."
  }
  "status" {
    Get-Ids
    $state = Aws ec2 describe-instances --instance-ids $Iid `
      --query "Reservations[0].Instances[0].State.Name" --output text
    Write-Host "Region: $Region  Instance: $Iid  State: $state  Bucket: $Bucket"
    if ($state -eq "running") {
      Invoke-Remote "if [ -e /opt/itov/SETUP_DONE ]; then echo SETUP: done; systemctl is-active comfyui; nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader; else echo SETUP: in progress; tail -n 5 /var/log/itov-setup.log; fi"
    }
  }
  "connect" {
    Get-Ids; Wait-Running
    $tmp = New-TemporaryFile
    '{"portNumber":["8188"],"localPortNumber":["8188"]}' | Set-Content $tmp -Encoding ascii
    Write-Host "Tunnel active: open http://localhost:8188  (Ctrl+C to close)"
    Start-Process "http://localhost:8188"
    & aws.exe ssm start-session --target $Iid --document-name AWS-StartPortForwardingSession `
      --parameters "file://$tmp" @Common
    Remove-Item $tmp -ErrorAction SilentlyContinue
  }
  "shell" { Get-Ids; & aws.exe ssm start-session --target $Iid @Common }
  "test" {
    Get-Ids
    $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$Root\tools\itov_test.py"))
    Write-Host "Generating a test clip (5 s, 832x480): a few minutes..."
    Invoke-Remote "echo $b64 | base64 -d > /tmp/itov_test.py && sudo -u comfy /opt/comfyui/venv/bin/python /tmp/itov_test.py"
    Write-Host "Download it with: .\itov.ps1 download <folder>"
  }
  "upload" {
    if (-not $Arg) { throw "usage: .\itov.ps1 upload <folder>" }
    Get-Ids
    Aws s3 sync $Arg "s3://$Bucket/input/" --sse AES256
    Invoke-Remote "/opt/itov/s3-sync.sh $Bucket pull"
    Write-Host "Images available in ComfyUI's 'Load Image' node."
  }
  "download" {
    if (-not $Arg) { throw "usage: .\itov.ps1 download <folder>" }
    Get-Ids
    Invoke-Remote "/opt/itov/s3-sync.sh $Bucket push"
    Aws s3 sync "s3://$Bucket/output/" $Arg
  }
  "wipe" {
    Get-Ids
    Invoke-Remote "/opt/itov/s3-sync.sh $Bucket wipe"
    Aws s3 rm "s3://$Bucket/" --recursive
    Write-Host "Input/output deleted from instance and bucket."
  }
  "destroy" {
    Get-Ids
    $ok = Read-Host "This deletes the instance, the disk and bucket '$Bucket' with all its content. Type DELETE to confirm"
    if ($ok -ne "DELETE") { Write-Host "Cancelled."; break }
    Aws s3 rm "s3://$Bucket/" --recursive
    Aws cloudformation delete-stack --stack-name $Stack
    Aws cloudformation wait stack-delete-complete --stack-name $Stack
    Aws s3api delete-bucket --bucket $Bucket
    Write-Host "Everything deleted."
  }
  default { Get-Help $PSCommandPath }
}
