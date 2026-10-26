# Sincronización labial mínima con MuseTalk 1.5 (código y modelo MIT, uso comercial permitido) en CPU.
# Reproduce la inferencia oficial (VAE sd-vae-ft-mse + UNet MuseTalkV15 + rasgos de audio de whisper-tiny)
# sin las dependencias de detección (mmpose): el recorte de la cara se define a mano en un cuadro de referencia
# y se sigue con template matching (la cabeza casi no se mueve). Solo se reemplaza la mitad inferior de la cara
# (boca, mentón) con una máscara elíptica difusa; ojos, anteojos y frente quedan originales.
#
# Uso: python lipsync_musetalk.py CUADROS_DIR AUDIO.wav SALIDA_DIR MODELOS_DIR x1 y1 x2 y2 cx cy rx ry [fps lx ly lrx lry top ramp]
#   top: borde superior de la mezcla; ramp: cuadros de entrada gradual de la boca generada (0 = corte seco)
#   lx ly lrx lry: elipse de los labios; fuera de ella se reinyecta el detalle fino del original
#   (bigote, barba, poros), que MuseTalk pierde al trabajar a 256 px.
#   CUADROS_DIR: PNG con la cara derecha (ya rotados), uno por cuadro de salida, ordenados por nombre.
#   x1 y1 x2 y2: recorte estilo MuseTalk en el primer cuadro (nariz en el centro vertical, mentón abajo).
#   cx cy rx ry: elipse de mezcla (boca/mentón) en el primer cuadro.
import sys, os, math, glob
import numpy as np, torch, cv2, librosa
from diffusers import AutoencoderKL, UNet2DConditionModel
from transformers import WhisperModel, AutoFeatureExtractor
import json

frames_dir, wav, out_dir, mdir = sys.argv[1:5]
x1, y1, x2, y2, cx, cy, rx, ry = map(int, sys.argv[5:13])
fps = int(sys.argv[13]) if len(sys.argv) > 13 else 24
lip = list(map(int, sys.argv[14:18])) if len(sys.argv) > 17 else None
top = int(sys.argv[18]) if len(sys.argv) > 18 else None   # borde superior de la mezcla (p. ej. justo arriba del labio)
ramp = int(sys.argv[19]) if len(sys.argv) > 19 else 0      # cuadros de entrada gradual (la boca original pasa a la generada)
os.makedirs(out_dir, exist_ok=True)
torch.set_num_threads(os.cpu_count())
dev = torch.device("cpu")

files = sorted(glob.glob(os.path.join(frames_dir, "*.png")))
frames = [cv2.imread(f) for f in files]
H, W = frames[0].shape[:2]

# --- seguimiento de la cabeza (traslación) con la zona de ojos/anteojos como plantilla ---
ty1, ty2 = y1 + int((y2 - y1) * 0.25), y1 + int((y2 - y1) * 0.5)
tx1, tx2 = x1 + int((x2 - x1) * 0.15), x1 + int((x2 - x1) * 0.85)
tmpl = cv2.cvtColor(frames[0][ty1:ty2, tx1:tx2], cv2.COLOR_BGR2GRAY)
offs = []
for fr in frames:
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    m = 80
    sx1, sy1 = max(0, tx1 - m), max(0, ty1 - m)
    win = g[sy1:min(H, ty2 + m), sx1:min(W, tx2 + m)]
    r = cv2.matchTemplate(win, tmpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(r)
    offs.append((loc[0] + sx1 - tx1, loc[1] + sy1 - ty1, score))
dx = np.array([o[0] for o in offs], float); dy = np.array([o[1] for o in offs], float)
k = 5; ker = np.ones(k) / k
dx = np.convolve(np.pad(dx, k // 2, mode="edge"), ker, "valid"); dy = np.convolve(np.pad(dy, k // 2, mode="edge"), ker, "valid")
print("seguimiento: dx %.1f..%.1f dy %.1f..%.1f score min %.2f" % (dx.min(), dx.max(), dy.min(), dy.max(), min(o[2] for o in offs)), flush=True)

# --- modelos ---
vae = AutoencoderKL.from_pretrained(os.path.join(mdir, "sd-vae")).to(dev).eval()
cfg = json.load(open(os.path.join(mdir, "musetalkV15", "musetalk.json")))
unet = UNet2DConditionModel(**cfg)
unet.load_state_dict(torch.load(os.path.join(mdir, "musetalkV15", "unet.pth"), map_location="cpu"))
unet.to(dev).eval()
whisper = WhisperModel.from_pretrained(os.path.join(mdir, "whisper")).to(dev).eval()
fe = AutoFeatureExtractor.from_pretrained(os.path.join(mdir, "whisper"))
sf = vae.config.scaling_factor

# codificación posicional (igual que MuseTalk)
d_model = 384; max_len = 5000
pe = torch.zeros(max_len, d_model); pos = torch.arange(0, max_len).float().unsqueeze(1)
div = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
pe[:, 0::2] = torch.sin(pos * div); pe[:, 1::2] = torch.cos(pos * div); pe = pe.unsqueeze(0)

# --- rasgos de audio por cuadro (get_whisper_chunk de MuseTalk, padding 2/2) ---
audio, sr = librosa.load(wav, sr=16000)
feats = []
for i in range(0, len(audio), 30 * sr):
    inp = fe(audio[i:i + 30 * sr], return_tensors="pt", sampling_rate=sr).input_features
    with torch.no_grad():
        hs = whisper.encoder(inp, output_hidden_states=True).hidden_states
    feats.append(torch.stack(hs, dim=2))
wf = torch.cat(feats, dim=1)
audio_fps = 50; mult = audio_fps / fps
num_frames = math.floor(len(audio) / sr * fps)
wf = wf[:, :math.floor(len(audio) / sr * audio_fps)]
pad = math.ceil(mult)
wf = torch.cat([torch.zeros_like(wf[:, :pad * 2]), wf, torch.zeros_like(wf[:, :pad * 3 * 2])], 1)
per = 2 * (2 + 2 + 1)
chunks = []
for f in range(num_frames):
    a = math.floor(f * mult)
    chunks.append(wf[:, a:a + per])
chunks = torch.cat(chunks, 0)                       # T, 10, 5, 384
chunks = chunks.reshape(chunks.shape[0], -1, 384)   # T, 50, 384
print("cuadros de audio:", num_frames, "cuadros de video:", len(frames), flush=True)
n = min(num_frames, len(frames))

norm = lambda x: (x - 0.5) / 0.5
yy, xx = np.mgrid[0:H, 0:W]

def blend_mask(ox, oy):
    e = (((xx - (cx + ox)) / rx) ** 2 + ((yy - (cy + oy)) / ry) ** 2)
    m = np.clip((1.15 - e) / 0.3, 0, 1)            # elipse con borde difuso
    m[: int(y1 + oy + (y2 - y1) * 0.5), :] = 0     # nunca por encima de la nariz (mitad superior intacta)
    if top is not None:
        ramp = np.clip((yy - (top + oy)) / 18.0, 0, 1)   # transición suave de 18 px arriba del labio
        m = m * ramp
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 6)
    return m[..., None]

for i in range(n):
    ox, oy = int(round(dx[i])), int(round(dy[i]))
    bx1, by1, bx2, by2 = x1 + ox, y1 + oy, x2 + ox, y2 + oy
    crop = cv2.resize(frames[i][by1:by2, bx1:bx2], (256, 256), interpolation=cv2.INTER_LANCZOS4)
    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    t = torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0)
    masked = t.clone(); masked[:, :, 128:, :] = 0
    with torch.no_grad():
        lm = sf * vae.encode(norm(masked)).latent_dist.sample()
        lr = sf * vae.encode(norm(t)).latent_dist.sample()
        lat = torch.cat([lm, lr], 1)
        a = chunks[i:i + 1] + pe[:, :chunks.shape[1]]
        pred = unet(lat, torch.tensor([0]), encoder_hidden_states=a).sample
        img = vae.decode(pred / sf).sample
    img = ((img / 2 + 0.5).clamp(0, 1)[0].permute(1, 2, 0).numpy() * 255).round().astype(np.uint8)
    res = cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), (bx2 - bx1, by2 - by1), interpolation=cv2.INTER_LANCZOS4)
    res = res.astype(np.float32); res = np.clip(res + 0.6 * (res - cv2.GaussianBlur(res, (0, 0), 1.6)), 0, 255).astype(np.uint8)  # nitidez (256 px reescalado)
    gen = frames[i].copy(); gen[by1:by2, bx1:bx2] = res
    if lip:
        o = frames[i].astype(np.float32)
        detail = o - cv2.GaussianBlur(o, (0, 0), 2.5)
        e = (((xx - (lip[0] + ox)) / lip[2]) ** 2 + ((yy - (lip[1] + oy)) / lip[3]) ** 2)
        lm_ = cv2.GaussianBlur(np.clip((1.2 - e) / 0.4, 0, 1).astype(np.float32), (0, 0), 5)[..., None]
        gen = np.clip(gen.astype(np.float32) + detail * (1 - lm_), 0, 255)
    m = blend_mask(ox, oy)
    if ramp and i < ramp:
        m = m * ((i + 1) / (ramp + 1))
    out = (gen.astype(np.float32) * m + frames[i].astype(np.float32) * (1 - m)).round().astype(np.uint8)
    cv2.imwrite(os.path.join(out_dir, "%04d.png" % i), out)
    if i % 10 == 0:
        print("cuadro", i, "/", n, flush=True)
print("listo", n)
