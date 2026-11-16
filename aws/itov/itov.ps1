<#
  itov - controllo della GPU AWS con ComfyUI + Wan 2.2

  .\itov.ps1 deploy          crea/aggiorna l'infrastruttura (una volta)
  .\itov.ps1 start           accende l'istanza
  .\itov.ps1 connect         apre il tunnel e ComfyUI su http://localhost:8188
  .\itov.ps1 stop            spegne l'istanza (si spegne anche da sola dopo 30 min di inattivita')
  .\itov.ps1 status          stato istanza + setup
  .\itov.ps1 upload <dir>    carica le immagini di una cartella in ComfyUI/input (via S3 cifrato)
  .\itov.ps1 download <dir>  scarica i video generati in una cartella locale
  .\itov.ps1 wipe            cancella input/output su istanza E bucket
  .\itov.ps1 shell           shell sull'istanza (via SSM)
  .\itov.ps1 test            genera una clip di prova con un'immagine sintetica
  .\itov.ps1 destroy         elimina TUTTO (istanza, disco, bucket)
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

function Aws { & aws.exe @args @Common; if ($LASTEXITCODE -ne 0) { throw "aws $($args[0..1] -join ' ') fallito" } }

function Out-Stack($key) {
  Aws cloudformation describe-stacks --stack-name $Stack `
    --query "Stacks[0].Outputs[?OutputKey=='$key'].OutputValue" --output text
}

function Get-Ids {
  $script:Iid    = Out-Stack "InstanceId"
  $script:Bucket = Out-Stack "BucketName"
}

function Wait-Running {
  Write-Host "Attendo che l'istanza sia pronta per SSM..."
  Aws ec2 wait instance-running --instance-ids $Iid
  for ($i = 0; $i -lt 60; $i++) {
    $s = Aws ssm describe-instance-information --filters "Key=InstanceIds,Values=$Iid" `
      --query "InstanceInformationList[0].PingStatus" --output text
    if ($s -eq "Online") { return }
    Start-Sleep 5
  }
  throw "L'agente SSM non risponde"
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
  if ($st -ne "Success") { throw "Comando remoto: $st" }
}

switch ($Cmd) {
  "deploy" {
    Aws cloudformation deploy --template-file "$Root\infra\itov.yaml" --stack-name $Stack `
      --capabilities CAPABILITY_IAM --no-fail-on-empty-changeset `
      --parameter-overrides "AvailabilityZone=$Arg" "InstanceType=$Type"
    Get-Ids
    Write-Host "Istanza: $Iid  Bucket: $Bucket"
    Write-Host "Il primo setup (ComfyUI + ~35GB di modelli) richiede ~20-30 min. Controlla con: .\itov.ps1 status"
  }
  "start" {
    Get-Ids; Aws ec2 start-instances --instance-ids $Iid | Out-Null; Wait-Running
    Write-Host "Accesa. Ora: .\itov.ps1 connect"
  }
  "stop" {
    Get-Ids; Aws ec2 stop-instances --instance-ids $Iid | Out-Null
    Write-Host "Spegnimento in corso (il disco con modelli e lavori resta)."
  }
  "status" {
    Get-Ids
    $state = Aws ec2 describe-instances --instance-ids $Iid `
      --query "Reservations[0].Instances[0].State.Name" --output text
    Write-Host "Regione: $Region  Istanza: $Iid  Stato: $state  Bucket: $Bucket"
    if ($state -eq "running") {
      Invoke-Remote "if [ -e /opt/itov/SETUP_DONE ]; then echo SETUP: completato; systemctl is-active comfyui; nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader; else echo SETUP: in corso; tail -n 5 /var/log/itov-setup.log; fi"
    }
  }
  "connect" {
    Get-Ids; Wait-Running
    $tmp = New-TemporaryFile
    '{"portNumber":["8188"],"localPortNumber":["8188"]}' | Set-Content $tmp -Encoding ascii
    Write-Host "Tunnel attivo: apri http://localhost:8188  (Ctrl+C per chiudere)"
    Start-Process "http://localhost:8188"
    & aws.exe ssm start-session --target $Iid --document-name AWS-StartPortForwardingSession `
      --parameters "file://$tmp" @Common
    Remove-Item $tmp -ErrorAction SilentlyContinue
  }
  "shell" { Get-Ids; & aws.exe ssm start-session --target $Iid @Common }
  "test" {
    Get-Ids
    $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$Root\tools\itov_test.py"))
    Write-Host "Genero una clip di prova (5 s, 832x480): qualche minuto..."
    Invoke-Remote "echo $b64 | base64 -d > /tmp/itov_test.py && sudo -u comfy /opt/comfyui/venv/bin/python /tmp/itov_test.py"
    Write-Host "Scaricala con: .\itov.ps1 download <cartella>"
  }
  "upload" {
    if (-not $Arg) { throw "uso: .\itov.ps1 upload <cartella>" }
    Get-Ids
    Aws s3 sync $Arg "s3://$Bucket/input/" --sse AES256
    Invoke-Remote "/opt/itov/s3-sync.sh $Bucket pull"
    Write-Host "Immagini disponibili nel nodo 'Load Image' di ComfyUI."
  }
  "download" {
    if (-not $Arg) { throw "uso: .\itov.ps1 download <cartella>" }
    Get-Ids
    Invoke-Remote "/opt/itov/s3-sync.sh $Bucket push"
    Aws s3 sync "s3://$Bucket/output/" $Arg
  }
  "wipe" {
    Get-Ids
    Invoke-Remote "/opt/itov/s3-sync.sh $Bucket wipe"
    Aws s3 rm "s3://$Bucket/" --recursive
    Write-Host "Input/output cancellati da istanza e bucket."
  }
  "destroy" {
    Get-Ids
    $ok = Read-Host "Elimino istanza, disco e bucket '$Bucket' con tutto il contenuto. Scrivi ELIMINA per confermare"
    if ($ok -ne "ELIMINA") { Write-Host "Annullato."; break }
    Aws s3 rm "s3://$Bucket/" --recursive
    Aws cloudformation delete-stack --stack-name $Stack
    Aws cloudformation wait stack-delete-complete --stack-name $Stack
    Aws s3api delete-bucket --bucket $Bucket
    Write-Host "Tutto eliminato."
  }
  default { Get-Help $PSCommandPath }
}
