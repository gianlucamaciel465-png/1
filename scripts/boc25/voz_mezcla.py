# Suma la voz de marca «Roccé — Firme 04» a un máster ya aprobado de BOC-25 sin tocar la imagen.
#   1. sintetiza cada frase del guion de voz con scripts/proxima/locucion.py (edge-tts + tratamiento Firme 04);
#   2. la ubica en su cuadro (30 fps) y controla que ninguna frase pise a la siguiente ni pase el final;
#   3. baja el fondo (audio del máster: música, efectos, hinchada) mientras habla la voz (ducking suave);
#   4. deja la voz ~12 dB arriba del fondo, medido frase por frase, y normaliza a −14 LUFS con pico ≤ −1 dBTP
#      (alimiter level=false);
#   5. arma el MP4 con el flujo de video copiado tal cual (mismo md5 de video que el máster aprobado).
#
# Uso: VOZ_PY=/home/user/envs/voz-env/bin/python python3 voz_mezcla.py GUION_VOZ.tsv MASTER.mp4 SALIDA.mp4 [TRABAJO_DIR]
#   GUION_VOZ.tsv: id<TAB>cuadro_de_entrada<TAB>texto a sintetizar   (Royé = Roccé, fáunders = founders)
#   Opcional por línea: 4.ª columna = atempo (p. ej. 1.06) para frases que no entran.
import os, sys, json, subprocess, re
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
LOC = os.path.join(AQUI, '..', 'proxima', 'locucion.py')
SR, FPS = 48000, 30
DUCK_DB, VOZ_SOBRE_FONDO = -9.0, 12.0

def leer(p, ch=2):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', p, '-vn', '-ac', str(ch), '-ar', str(SR), '-f', 'f32le', '-'],
                                  stdin=subprocess.DEVNULL)
    return np.frombuffer(raw, np.float32).astype(np.float64).reshape(-1, ch)

def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)

def lufs(path):
    o = subprocess.run(['ffmpeg', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    i = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1]); tp = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', o)[-1])
    return i, tp

def main():
    guion, master, salida = sys.argv[1:4]
    trab = sys.argv[4] if len(sys.argv) > 4 else os.path.splitext(salida)[0] + '_voz'
    os.makedirs(trab, exist_ok=True)
    filas = []
    for l in open(guion, encoding='utf-8'):
        if not l.strip() or l.startswith('#'): continue
        c = l.rstrip('\n').split('\t')
        filas.append(dict(id=c[0], cuadro=int(c[1]), texto=c[2], atempo=float(c[3]) if len(c) > 3 and c[3] else 1.0))
    tsv = os.path.join(trab, 'sintesis.tsv')
    with open(tsv, 'w', encoding='utf-8') as f:
        for r in filas: f.write(f"{r['id']}\t{r['texto']}\n")
    subprocess.run(['python3', LOC, tsv, trab], check=True)

    fondo = leer(master)
    n = len(fondo); dur = n / SR
    voz = np.zeros(n); mascara = np.zeros(n)
    informe = []
    for k, r in enumerate(filas):
        w = os.path.join(trab, f"{r['id']}.wav")
        if r['atempo'] != 1.0:
            w2 = os.path.join(trab, f"{r['id']}_t.wav")
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', w, '-af', f"atempo={r['atempo']}", w2], check=True)
            w = w2
        x = leer(w, 1)[:, 0]
        x = x / (np.sqrt(np.mean(x ** 2)) + 1e-12) * 0.1          # todas las frases al mismo RMS antes de mezclar
        a = int(round(r['cuadro'] / FPS * SR)); b = min(n, a + len(x))
        fin = b / SR
        sig = filas[k + 1]['cuadro'] / FPS if k + 1 < len(filas) else dur
        aviso = ''
        if a + len(x) > n - int(0.25 * SR): aviso = 'PASA EL FINAL'
        elif fin > sig - 0.08: aviso = f'PISA LA SIGUIENTE ({fin - sig + 0.08:+.2f} s)'
        voz[a:b] += x[:b - a]; mascara[a:b] = 1
        informe.append(dict(id=r['id'], entra=round(a / SR, 3), sale=round(fin, 3), dur=round(len(x) / SR, 3),
                            texto=r['texto'], atempo=r['atempo'], aviso=aviso))
    # ducking: envolvente suave de la máscara (ataque 40 ms, relajación 300 ms)
    env = np.zeros(n); g = 0.0
    at, rel = np.exp(-1 / (0.04 * SR)), np.exp(-1 / (0.30 * SR))
    for i in range(n):
        t = mascara[i]; c = at if t > g else rel; g = c * g + (1 - c) * t; env[i] = g
    fondo_d = fondo * (10 ** (DUCK_DB * env / 20))[:, None]
    # nivel de voz: mediana de (fondo bajado en cada frase) + 12 dB; cada frase queda entre +10 y +15 dB
    vg = np.ones(n)
    diffs = []
    bases = []
    for r in informe:
        a, b = int(r['entra'] * SR), int(r['sale'] * SR)
        bases.append(rms_db(fondo_d[a:b]))
    ref = float(np.median(bases)) + VOZ_SOBRE_FONDO
    for r, base in zip(informe, bases):
        a, b = int(r['entra'] * SR), int(r['sale'] * SR)
        vd = rms_db(voz[a:b])
        objetivo = ref
        if objetivo - base < 10: objetivo = base + 10
        if objetivo - base > 15 and base > -60: objetivo = max(ref - 3, base + 15)
        gdb = objetivo - vd
        vg[a:b] = 10 ** (gdb / 20)
        r['voz_sobre_fondo_db'] = round(objetivo - base, 1)
    vozf = voz * vg
    mezcla = fondo_d + vozf[:, None]
    tmp = os.path.join(trab, 'mezcla_pre.wav'); fin_wav = os.path.join(trab, 'mezcla.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f64le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'pcm_f32le', tmp],
                   input=mezcla.astype(np.float64).tobytes(), check=True)
    i0, _ = lufs(tmp)
    gan = -14.0 - i0
    for _ in range(3):   # el limitador come sonoridad: se corrige la ganancia hasta quedar en −14 ± 0,3
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af',
                        f'volume={gan:.2f}dB,alimiter=limit=0.84:level=false:attack=3:release=60', '-ar', str(SR), '-c:a', 'pcm_f32le', fin_wav],
                       check=True)
        i1, tp1 = lufs(fin_wav)
        if abs(i1 + 14.0) <= 0.3: break
        gan += -14.0 - i1
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', master, '-i', fin_wav, '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '192k', '-ar', str(SR), '-ac', '2', '-shortest', '-movflags', '+faststart',
                    '-map_metadata', '-1', salida], check=True)
    md5v = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', salida, '-map', '0:v', '-f', 'md5', '-'], text=True).strip()
    md5m = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', master, '-map', '0:v', '-f', 'md5', '-'], text=True).strip()
    i2, tp2 = lufs(salida)
    durs = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,duration', '-of', 'csv=p=0', salida], text=True)
    res = dict(master=master, salida=salida, video_md5_master=md5m, video_md5_salida=md5v, video_igual=md5m == md5v,
               lufs=i2, pico_dbtp=tp2, duraciones=durs.strip().splitlines(), ducking_db=DUCK_DB, frases=informe)
    json.dump(res, open(os.path.join(trab, 'voz_mezcla.json'), 'w'), indent=1, ensure_ascii=False)
    for r in informe:
        print(f"{r['id']:>4} {r['entra']:6.2f}–{r['sale']:6.2f}  +{r.get('voz_sobre_fondo_db', 0):4.1f} dB  {r['aviso']:<24} {r['texto']}")
    print(f"LUFS {i2:.1f}  pico {tp2:.1f} dBTP  video igual al máster: {md5m == md5v}  {durs.strip()}")

if __name__ == '__main__':
    main()
