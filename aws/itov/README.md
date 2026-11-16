# itov — Image-to-video privato su AWS

Trasforma immagini in brevi video (clip di ~5 s) con **ComfyUI + Wan 2.2 I2V 14B** su una GPU NVIDIA
nel **tuo** account AWS. Le immagini non escono dall'account: nessun servizio esterno, nessuna porta aperta.

```
aws/itov/
├── itov.ps1            script di controllo (deploy, start, connect, stop, ...)
├── infra/itov.yaml     CloudFormation: GPU, disco e bucket cifrati, accesso solo SSM
├── tools/itov_test.py  test end-to-end con un'immagine sintetica
└── NOTES.md            GPU/regioni, quote, costi, problemi comuni
```

## Requisiti
- **Windows** con PowerShell (lo script è `.ps1`).
- [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) e un utente IAM con permessi su
  CloudFormation, EC2, IAM, S3 e SSM.
- [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)
  per la AWS CLI.
- Quota GPU nella regione scelta (vedi passo 2).

## Guida rapida (da zero)

### 1. Clona e configura le credenziali
```powershell
git clone https://github.com/stefacc/toolbox.git
cd toolbox\aws\itov
aws configure --profile itov          # access key, secret key, region (es. eu-west-3)
aws sts get-caller-identity --profile itov   # deve rispondere con il tuo account
```
Se Windows blocca gli script, usa in tutti i comandi seguenti
`powershell -ExecutionPolicy Bypass -File .\itov.ps1 <comando>`
oppure, una volta sola: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### 2. Scegli regione e GPU (e controlla la quota)
Di default: regione **eu-west-3** (Parigi) con **g6.2xlarge** (NVIDIA L4 24 GB, ~1,2 $/h).
Per cambiarli, prima del deploy:
```powershell
$env:ITOV_REGION = "eu-north-1"     # es. Stoccolma
$env:ITOV_TYPE   = "g6e.xlarge"     # L40S 48 GB, più veloce (~2 $/h), non disponibile in tutte le regioni
```
La quota **"Running On-Demand G and VT instances"** della regione deve essere ≥ vCPU della macchina
(8 per g6.2xlarge). Verifica:
```powershell
aws service-quotas get-service-quota --service-code ec2 --quota-code L-DB2E81BA --profile itov --region eu-west-3
```
Se è 0, chiedi l'aumento da console *Service Quotas* (approvazione da poche ore a un giorno).

### 3. Deploy
```powershell
.\itov.ps1 deploy               # opzionale: .\itov.ps1 deploy eu-west-3a  (availability zone specifica)
```
Se fallisce con *insufficient capacity*, la GPU è esaurita in quella zona: riprova con un'altra AZ, regione o tipo
(prima esegui `aws cloudformation delete-stack --stack-name itov --profile itov --region <regione>`).

### 4. Attendi il setup (~25 min, solo la prima volta)
```powershell
.\itov.ps1 status               # "SETUP: in corso" → "SETUP: completato"
```
L'istanza installa ComfyUI e scarica ~35 GB di modelli.

### 5. (Opzionale) Test
```powershell
.\itov.ps1 test                 # genera una clip di prova (~5 min su L4)
.\itov.ps1 download .\output    # scarica i video generati
```

### 6. Usa ComfyUI
```powershell
.\itov.ps1 connect              # apre http://localhost:8188 — lascia aperta la finestra (è il tunnel)
```
In ComfyUI: **Workflow → Browse Templates → Video → "Wan 2.2 14B Image to Video"**, carica l'immagine nel nodo
*Load Image*, descrivi il movimento nel prompt e premi **Run**. Il template con LoRA lightx2v a 4 step è molto più veloce.

### 7. A fine lavoro
```powershell
.\itov.ps1 stop                 # spegne (si spegne comunque da sola dopo 30 min di inattività a tunnel chiuso)
.\itov.ps1 destroy              # elimina TUTTO: istanza, disco con modelli, bucket
```

## Tutti i comandi
| Comando | Cosa fa |
|---|---|
| `deploy [az]` | crea/aggiorna l'infrastruttura |
| `start` / `stop` | accende / spegne l'istanza (il disco resta) |
| `status` | stato istanza e avanzamento setup |
| `connect` | tunnel SSM + apre ComfyUI su `localhost:8188` |
| `upload <cartella>` | carica immagini in ComfyUI/input (via S3 cifrato) |
| `download <cartella>` | scarica i video generati |
| `wipe` | cancella input/output da istanza e bucket |
| `test` | clip di prova con immagine sintetica |
| `shell` | shell sull'istanza (via SSM) |
| `destroy` | elimina tutto |

## Sicurezza
- Istanza **senza porte in ingresso**: accesso solo tramite AWS SSM (tunnel cifrato, autenticato con IAM).
- ComfyUI ascolta solo su `127.0.0.1` dell'istanza; i nodi "API" (servizi cloud esterni) sono disattivati.
- Disco EBS e bucket S3 **cifrati**; bucket con Block Public Access e solo HTTPS.
- Internet in uscita serve solo per il setup (pacchetti e pesi del modello da Hugging Face).
- Se un antivirus/proxy ispeziona HTTPS, escludi `*.amazonaws.com` e `*.aws.amazon.com`: altrimenti la CLI fallisce
  e il proxy vedrebbe il traffico.

## Costi indicativi
- GPU accesa: g6.2xlarge ~1,2 $/h · g6e.xlarge ~2 $/h. Spenta: 0 $ di calcolo.
- Disco 200 GB: ~18 $/mese **anche a istanza spenta** → `destroy` quando non serve più.
- Consigliato un AWS Budget con avvisi email (vedi [NOTES.md](NOTES.md)).
