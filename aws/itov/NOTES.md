# itov — note tecniche

## Prerequisiti
- Utente/ruolo IAM con permessi su CloudFormation, EC2, IAM, S3, SSM.
- Profilo CLI `itov`:
  ```powershell
  aws configure --profile itov     # region es. eu-west-3
  ```
- Session Manager plugin installato (serve per `connect` e `shell`).

## Scelta di regione e GPU
| Tipo | GPU | Note |
|---|---|---|
| g6e.xlarge / 2xlarge | L40S 48 GB | più veloce; non offerta in tutte le regioni UE (es. assente a Milano, Irlanda, Londra, Parigi) |
| g6.2xlarge | L4 24 GB | economica; Wan 2.2 14B fp8 gira con swap tra i due modelli |
| g5.2xlarge | A10G 24 GB | alternativa alla L4 |

- Le GPU on-demand possono risultare esaurite (`InsufficientInstanceCapacity`): provare altre AZ, altre regioni o altri tipi.
- Per verificare la capacità rapidamente: `aws ec2 run-instances` su una AZ specifica e `terminate-instances` subito dopo
  (molto più veloce che attendere il rollback di CloudFormation).
- La quota "Running On-Demand G and VT instances" è **per regione** e può essere 0: chiederne l'aumento in Service Quotas
  (4 vCPU per g6e.xlarge, 8 per g6e.2xlarge / g6.2xlarge).

## Tempi e costi indicativi
- Setup al primo avvio: ~25 min (pacchetti, ComfyUI, ~35 GB di modelli). Log: `/var/log/itov-setup.log`.
- Clip 5 s, 832x480, 81 frame, LoRA 4 step su L4: ~5 min al primo run (~0,10 $).
- On-demand: g6.2xlarge ~1,2 $/h, g6e.xlarge ~2 $/h, g6e.2xlarge ~2,4 $/h (variano per regione).
- Disco 200 GB gp3 ≈ 18–19 $/mese anche a istanza spenta.

## Problemi comuni
- **Antivirus/proxy con ispezione HTTPS** → la CLI dà `CERTIFICATE_VERIFY_FAILED`.
  Soluzione: escludere `*.amazonaws.com` e `*.aws.amazon.com` dall'ispezione (altrimenti il traffico è visibile al proxy).
- **Git Bash** riscrive gli argomenti che iniziano con `/` (es. nomi di parametri SSM) → `export MSYS_NO_PATHCONV=1`.
- Dopo l'installazione del Session Manager plugin le console già aperte non lo trovano nel PATH
  (`itov.ps1` lo aggiunge automaticamente).
- Un **tunnel lasciato aperto** impedisce l'auto-spegnimento: chiuderlo a fine lavoro.
- Il bucket ha `DeletionPolicy: Retain`: `destroy` lo svuota e lo cancella a parte.

## Budget (opzionale, fuori dallo stack)
AWS Budget mensile con avvisi email a 50/80/100% + previsione, e budget action `STOP_EC2_INSTANCES`
sull'instance id al 100% (ruolo IAM con policy `AWSBudgetsActions_RolePolicyForResourceAdministrationWithSSM`).
Va aggiornata a ogni nuova istanza e cancellata a mano quando si elimina tutto.
