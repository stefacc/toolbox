import json, time, urllib.request
from PIL import Image, ImageDraw

# immagine sintetica di prova
W, H = 832, 480
img = Image.new("RGB", (W, H))
d = ImageDraw.Draw(img)
for y in range(H):
    d.line([(0, y), (W, y)], fill=(30 + y // 6, 80 + y // 5, 160 + y // 8))
d.ellipse([560, 60, 700, 200], fill=(255, 210, 90))
d.polygon([(0, 480), (250, 250), (500, 480)], fill=(40, 90, 60))
d.polygon([(300, 480), (600, 220), (832, 480)], fill=(30, 70, 50))
img.save("/opt/comfyui/input/itov_test.png")

M = "wan2.2_i2v_{}_noise_14B_fp8_scaled.safetensors"
L = "wan2.2_i2v_lightx2v_4steps_lora_v1_{}_noise.safetensors"
wf = {
  "1": {"class_type": "UNETLoader", "inputs": {"unet_name": M.format("high"), "weight_dtype": "default"}},
  "2": {"class_type": "UNETLoader", "inputs": {"unet_name": M.format("low"), "weight_dtype": "default"}},
  "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": L.format("high"), "strength_model": 1.0}},
  "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["2", 0], "lora_name": L.format("low"), "strength_model": 1.0}},
  "5": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["3", 0], "shift": 5.0}},
  "6": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": 5.0}},
  "7": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
  "8": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": "slow cinematic camera push-in over green hills at sunset, clouds drifting, warm light"}},
  "9": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": "blurry, low quality, distorted, static, watermark, text"}},
  "10": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
  "11": {"class_type": "LoadImage", "inputs": {"image": "itov_test.png"}},
  "12": {"class_type": "WanImageToVideo", "inputs": {"positive": ["8", 0], "negative": ["9", 0], "vae": ["10", 0], "start_image": ["11", 0], "width": W, "height": H, "length": 81, "batch_size": 1}},
  "13": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["5", 0], "add_noise": "enable", "noise_seed": 42, "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["12", 2], "start_at_step": 0, "end_at_step": 2, "return_with_leftover_noise": "enable"}},
  "14": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["6", 0], "add_noise": "disable", "noise_seed": 0, "steps": 4, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["13", 0], "start_at_step": 2, "end_at_step": 10000, "return_with_leftover_noise": "disable"}},
  "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["10", 0]}},
  "16": {"class_type": "CreateVideo", "inputs": {"images": ["15", 0], "fps": 16}},
  "17": {"class_type": "SaveVideo", "inputs": {"video": ["16", 0], "filename_prefix": "video/itov_test", "format": "auto", "codec": "auto"}},
}

API = "http://127.0.0.1:8188"
req = urllib.request.Request(API + "/prompt", data=json.dumps({"prompt": wf}).encode(), headers={"Content-Type": "application/json"})
try:
    pid = json.load(urllib.request.urlopen(req))["prompt_id"]
except urllib.error.HTTPError as e:
    print("ERRORE workflow:", e.read().decode()[:2000]); raise SystemExit(1)

t0 = time.time()
while True:
    time.sleep(5)
    h = json.load(urllib.request.urlopen(f"{API}/history/{pid}"))
    if pid in h:
        st = h[pid]["status"]
        print("stato:", st.get("status_str"), "| tempo: %.0f s" % (time.time() - t0))
        if st.get("status_str") != "success":
            print(json.dumps(st.get("messages", []))[-2000:])
        for n in h[pid]["outputs"].values():
            for k, v in n.items():
                if isinstance(v, list):
                    for f in v:
                        if isinstance(f, dict) and "filename" in f:
                            print("output:", f.get("subfolder"), f["filename"])
        break
    if time.time() - t0 > 3000:
        print("timeout"); break
