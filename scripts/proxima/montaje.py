# Montaje de ROCCE_proxima ("La próxima empieza con vos"). La línea de tiempo se calcula con la duración y las palabras
# de cada frase de la locución (Firme 04), con los cortes sobre la grilla de la música (104 BPM, origen en el corte a la ola).
#
# Historia (StoryBrand): el héroe es quien mira y guarda una idea para "algún día" (villano: postergar).
# Roccé es el guía: también fue una idea; Gianluca la construye mientras labura en una fábrica, y cada detalle se decidió.
# Plan: el 01/11 los primeros 100 en comprar son founders; el founder 001 diseña una prenda y se lleva un porcentaje
# de la ganancia. Acción de hoy: escribir FOUNDERS por mensaje. Éxito: que la próxima Roccé empiece con vos.
#
#   A   IMG_3453  macro, dedos sobre "ROCCÉ / so f★cking close." (negra) .... "¿Hace cuánto que guardás esa idea?"
#   B   IMG_7887  rompe una ola; Gianluca saca la foto de la blanca .......... "Roccé también empezó como una idea."
#   C   IMG_7884  por encima de su hombro hasta la blanca ..................... "Gianluca la construye mientras labura…"
#   D1  IMG_8004  DENIM · D2 IMG_7793 TONO SOBRE TONO · D3 IMG_3375 LA FRASE .. "Cada detalle lo decidimos nosotros."
#   E   IMG_7857  la blanca puesta frente al mar (respiro) .................... "La próxima Roccé puede empezar con vos."
#   F1  IMG_4631  la ola crece y rompe sobre las dos (ALGÚN DÍA tachado → 01/11) "El primero de noviembre, los primeros cien…"
#   F2a IMG_4530  la blanca sostenida (FOUNDER 001) ........................... "El founder 001 diseña una prenda"
#   F2b IMG_7824  la negra viene hacia cámara (UN PORCENTAJE) ................. "y se lleva un porcentaje de la ganancia."
#   G   IMG_7896  placa de la casa: Escribinos [FOUNDERS] ...................... "Escribinos FOUNDERS hoy y conocé cómo participar."
#
# Uso: python3 montaje.py VOZ_DIR SALIDA.mp4
#   VOZ_DIR = salida de locucion.py + palabras.py (L1.wav … L8.wav + locucion.json)
#   Variables: S (scratchpad con voz-env), MEDIR=1 (además mide voz contra fondo), SOLO_LINEA=1 (solo la línea de tiempo)
import os, sys, json, math, subprocess

voz_dir, salida = sys.argv[1], sys.argv[2]
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); os.chdir(R)
T = "TRABAJO/proxima"; C = f"{T}/clips"; os.makedirs(C, exist_ok=True)
S = os.environ.get("S", "/tmp/claude-0/-home-user-1/bd43937f-7b34-55cc-a48c-8ac864032e15/scratchpad")
VPY = os.environ.get("VOZ_PY", f"{S}/voz-env/bin/python")
FPS, BPM = 30, 104; BEAT = 60 / BPM
O = lambda n: f"ORIGINALES/{n}.mov"
q = lambda t: round(round(t * FPS) / FPS, 4)

loc = json.load(open(os.path.join(voz_dir, "locucion.json")))
V = {f["id"]: f["duracion"] for f in loc["frases"]}
PAL = {f["id"]: f.get("palabras", []) for f in loc["frases"]}
def w(lid, pref, defecto):
    for p, a, b in PAL[lid]:
        if p.lower().strip("¿?,.").startswith(pref): return a
    return defecto

# ---------- línea de tiempo ----------
t = {"L1": 0.10}
B0 = q(t["L1"] + V["L1"] + 0.22)                      # corte a la ola: origen de la grilla
def snap(x, paso=0.5):                                # a la corchea siguiente de la grilla (o a la anterior si está muy cerca)
    b = BEAT * paso; k = math.ceil((x - B0) / b - 0.2); return q(B0 + k * b)
t["L2"] = B0 + 0.25
C0 = snap(t["L2"] + V["L2"] + 0.06); t["L3"] = C0 + 0.12
D0 = snap(t["L3"] + V["L3"] + 0.28); t["L4"] = D0 + 0.08
D1 = q(D0 + 1.5 * BEAT); D2 = q(D0 + 3 * BEAT); E0 = q(D0 + 5 * BEAT)
t["L5"] = E0 + 0.22
F1 = snap(t["L5"] + V["L5"] + 0.32); t["L6"] = F1 + 0.12
F2a = snap(t["L6"] + V["L6"] + 0.08); t["L7"] = F2a + 0.10
F2b = snap(t["L7"] + w("L7", "y", 2.42) - 0.06, 0.5)
G0 = snap(t["L7"] + V["L7"] + 0.18); t["L8"] = G0 + 0.35
FIN = q(t["L8"] + V["L8"] + 2.2)
assert t["L4"] + V["L4"] < E0, "la frase de los detalles no entra en D"
cortes = [("A", 0, B0), ("B", B0, C0), ("C", C0, D0), ("D1", D0, D1), ("D2", D1, D2), ("D3", D2, E0), ("E", E0, F1),
          ("F1", F1, F2a), ("F2a", F2a, F2b), ("F2b", F2b, G0), ("G", G0, FIN)]
dd = {k: b - a for k, a, b in cortes}
# entradas en las tomas originales
inp = {"A": 0.30, "B": 0.0, "C": max(0.3, 4.55 - dd["C"]), "D1": 3.05, "D2": 2.35, "D3": 0.50, "E": 1.00,
       "F1": max(0.0, 3.0 - (t["L6"] - F1) - w("L6", "los", 1.36)),           # el golpe de la ola (3,0 s) cae en "los primeros cien"
       "F2a": max(0.0, min(0.8, 3.12 - dd["F2a"])), "F2b": 4.20, "G": max(0.3, 6.15 - dd["G"])}
src = {"A": "IMG_3453", "B": "IMG_7887", "C": "IMG_7884", "D1": "IMG_8004", "D2": "IMG_7793", "D3": "IMG_3375", "E": "IMG_7857",
       "F1": "IMG_4631", "F2a": "IMG_4530", "F2b": "IMG_7824", "G": "IMG_7896"}

# ---------- textos (ver textos.py) ----------
tx = [dict(id="A_pregunta", t0=0.0, t1=B0, fi=0),
      dict(id="grad_inf", t0=B0, t1=C0, fi=0), dict(id="B_nombre", t0=B0 + 0.40, t1=C0),
      dict(id="grad_sup", t0=C0, t1=D0, fi=0), dict(id="C_espera", t0=t["L3"] + w("L3", "labura", 1.32) - 0.10, t1=D0),
      dict(id="grad_sup", t0=D0, t1=E0, fi=0), dict(id="D_denim", t0=D0, t1=D1, fi=0.10),
      dict(id="D_tono", t0=D1, t1=D2, fi=0.10), dict(id="D_frase", t0=D2, t1=E0, fi=0.10),
      dict(id="grad_sup_l", t0=E0, t1=F1, fi=0), dict(id="E_tesis", t0=E0 + 0.15, t1=F1),
      dict(id="grad_f1", t0=F1, t1=F2a, fi=0)]
t_cien = t["L6"] + w("L6", "los", 1.36) - 0.06; t_tacha = t["L6"] + w("L6", "noviembre", 0.58)
tx += [dict(id="F1_algun", t0=F1 + 0.02, t1=F2a, tachar=t_tacha, fi=0.10),      # "algún día" tachado queda arriba
       dict(id="F1_fecha", t0=t_tacha + 0.20, t1=F2a, fi=0.12),                      # 01/11 queda todo el tramo
       dict(id="F1_cien", t0=t_cien, t1=F2a),
       dict(id="grad_sup", t0=F2a, t1=F2b, fi=0), dict(id="F2_001", t0=F2a + 0.05, t1=F2b),
       dict(id="grad_sup_l", t0=F2b, t1=G0, fi=0), dict(id="F2_pct", t0=F2b + 0.04, t1=G0)]
t_found = t["L8"] + w("L8", "no", 0.44) - 0.04
tx += [dict(id="grad_fuerte", t0=G0, t1=FIN, fi=0), dict(id="G_escribinos", t0=G0 + 0.10, t1=FIN),
       dict(id="G_burbuja", t0=t_found, t1=FIN, fi=0.12), dict(id="G_ruta", t0=t["L8"] + w("L8", "hoy", 0.9), t1=FIN),
       dict(id="G_participar", t0=t["L8"] + w("L8", "y", 1.2), t1=FIN),
       dict(id="grad_inf", t0=t["L8"] + V["L8"] - 0.45, t1=FIN, fi=0.3), dict(id="G_datos", t0=t["L8"] + V["L8"] - 0.35, t1=FIN, fi=0.2)]

# ---------- música y efectos ----------
musica = dict(bpm=BPM, origen=B0, tramos=[
    dict(tipo="intro", desde=0.0, hasta=B0), dict(tipo="pulso", desde=B0, hasta=E0, charles_desde=C0),
    dict(tipo="respiro", desde=E0, hasta=F1), dict(tipo="subida", desde=F1, hasta=G0),
    dict(tipo="pleno", desde=G0, hasta=snap(FIN - 1.3)), dict(tipo="cola", desde=snap(FIN - 1.3), hasta=FIN)])
fx = [dict(tipo="roce", t=0.25, dur=1.1, db=-14),
      dict(tipo="golpe", t=B0, db=-9),
      dict(tipo="clic", t=D0, db=-12), dict(tipo="clic", t=D1, db=-12), dict(tipo="clic", t=D2, db=-12),
      dict(tipo="subida", t=F1, dur=min(1.6, F1 - (t["L5"] + V["L5"]) + 0.6), db=-8), dict(tipo="golpe", t=F1, db=-8),
      dict(tipo="barrido", t=t_tacha, db=-13),
      dict(tipo="clic", t=F2a, db=-14), dict(tipo="clic", t=F2b, db=-14),
      dict(tipo="subida", t=G0, dur=4 * BEAT, db=-9), dict(tipo="golpe", t=G0, db=-5),
      dict(tipo="clic", t=t_found, db=-16)]
lin = dict(duracion=FIN, voz=V, inicio_frases={k: round(v, 3) for k, v in t.items()},
           cortes={k: [a, b] for k, a, b in cortes}, entradas=inp, tomas=src, textos=tx, musica=musica, fx=fx)
json.dump(lin, open(f"{T}/linea_de_tiempo.json", "w"), indent=1, ensure_ascii=False)
for k, a, b in cortes: print(f"{k:4s} {a:6.3f}–{b:6.3f} ({b - a:4.2f} s)  {src[k]} desde {inp[k]:.2f}")
print("frases:", {k: round(v, 2) for k, v in t.items()}, "duración", FIN)
if os.environ.get("SOLO_LINEA"): sys.exit(0)

# ---------- tomas ----------
ENC = ["-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
       "-color_trc", "bt709", "-colorspace", "bt709", "-an"]
SC = "scale=1080:1920:flags=lanczos:out_range=tv,format=yuv420p,fps=30,setsar=1"
TM = "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
VF = {"A": f"{TM},colorchannelmixer=rr=0.84:gg=0.98:bb=1.16,eq=gamma=0.66:saturation=0.5,fps=30,scale=1080:1920:flags=lanczos,setsar=1",
      "D3": f"{TM},colorchannelmixer=rr=0.88:gg=1.0:bb=1.12,fps=30,scale=1080:1920:flags=lanczos,setsar=1",
      "F1": f"{TM},fps=30,scale=1080:1920:flags=lanczos,setsar=1",
      "F2a": f"{TM},colorchannelmixer=rr=1.05:gg=1.03:bb=0.92,fps=30,scale=1080:1920:flags=lanczos,setsar=1",
      "G": "crop=w=iw/1.16:h=ih/1.16:x=iw*0.024:y=ih*0.07,scale=1080:1920:flags=lanczos:in_range=pc:out_range=tv,format=yuv420p,fps=30,setsar=1"}
nf = lambda a, b: int(round((b - a) * FPS))
lista = []; SOLO_AUDIO = bool(os.environ.get("SOLO_AUDIO"))     # SOLO_AUDIO=1: rehace solo música y mezcla
for k, a, b in cortes:
    f = f"{C}/{k}.mp4"; lista.append(f)
    if SOLO_AUDIO: continue
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{inp[k]:.3f}", "-i", O(src[k]), "-vf", VF.get(k, SC),
                    "-frames:v", str(nf(a, b))] + ENC + [f], check=True, stdin=subprocess.DEVNULL)
    n = int(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                                      "stream=nb_read_frames", "-of", "csv=p=0", f]).decode())
    assert n == nf(a, b), f"{k}: {n} cuadros (esperados {nf(a, b)}): la toma no alcanza"

# ---------- textos, música, efectos ----------
if not SOLO_AUDIO: subprocess.run(["python3", "scripts/proxima/textos.py", f"{T}/linea_de_tiempo.json", f"{T}/textos"], check=True)
subprocess.run([VPY, "-I", "scripts/proxima/musica.py", f"{T}/linea_de_tiempo.json", f"{T}/audio"], check=True)

# ---------- mezcla ----------
ms = lambda s: int(round(s * 1000))
AF = "aresample=48000,aformat=channel_layouts=stereo"
def mezcla(destino, voz_oir=0.0, mus_db=0.0, amb_db=0.0, fx_db=0.0, gan=0.0, limite=None):
    ins = []
    for i in range(1, 9): ins += ["-i", os.path.join(voz_dir, f"L{i}.wav")]                         # 0–7
    ins += ["-i", f"{T}/audio/musica.wav", "-i", f"{T}/audio/fx.wav"]                                 # 8, 9
    amb = [("B", 0.0, 1.0), ("C", -10, 0.15), ("E", -12, 0.25), ("F1", -15, 0.15), ("F2a", -16, 0.1), ("F2b", -16, 0.1), ("G", -6, 0.2)]
    for k, _, _ in amb: ins += ["-i", O(src[k])]                                                       # 10…
    voz = ";".join(f"[{i}:a]{AF},highpass=f=80,acompressor=threshold=0.1:ratio=2.5:attack=5:release=120:makeup=1.3,"
                   f"adelay={ms(t[f'L{i + 1}'])}|{ms(t[f'L{i + 1}'])}[v{i}]" for i in range(8))
    ambs = []
    for j, (k, db, fade) in enumerate(amb):
        a, b = dict((c[0], c[1:]) for c in cortes)[k]; d = b - a
        vol = f"volume={db}dB" if k != "B" else "volume='if(lt(t,0.22),1.5,max(0.20,1.5-(t-0.22)*6))':eval=frame"
        ambs.append(f"[{10 + j}:a]{AF},atrim={inp[k]:.3f}:{inp[k] + d + 0.25:.3f},asetpts=PTS-STARTPTS,{vol},"
                    f"afade=t=in:d={fade},afade=t=out:st={max(0.0, d - 0.05):.3f}:d=0.3,adelay={ms(a)}|{ms(a)}[e{j}]")
    fc = f"""{voz};
[v0][v1][v2][v3][v4][v5][v6][v7]amix=inputs=8:normalize=0:duration=longest,apad=whole_dur={FIN:.3f},asplit=4[voz0][sc1][sc2][sc3];[voz0]volume={voz_oir}dB[voz];
[8:a]{AF},volume={mus_db}dB[mus0];[mus0][sc1]sidechaincompress=threshold=0.02:ratio=6:attack=10:release=260:makeup=1[mus];
{';'.join(ambs)};
{''.join(f'[e{j}]' for j in range(len(amb)))}amix=inputs={len(amb)}:normalize=0:duration=longest,volume={amb_db}dB[amb0];
[amb0][sc2]sidechaincompress=threshold=0.03:ratio=3:attack=10:release=250:makeup=1[amb];
[9:a]{AF},volume={fx_db}dB[fx0];[fx0][sc3]sidechaincompress=threshold=0.03:ratio=3:attack=8:release=220:makeup=1[fx];
[voz][mus][amb][fx]amix=inputs=4:normalize=0:duration=longest,atrim=0:{FIN:.3f},volume={gan}dB{',alimiter=limit=%s:attack=3:release=60:level=false' % limite if limite else ''}[au]"""
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", fc, "-map", "[au]", "-c:a", "pcm_s24le", destino],
                   check=True, stdin=subprocess.DEVNULL)
    dur_a = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", destino]).decode())
    assert abs(dur_a - FIN) < 0.03, f"la mezcla dura {dur_a:.2f} s y el video {FIN:.2f} s"

def lufs(p):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float(r.split("Integrated loudness:")[1].split("I:")[1].split("LUFS")[0]); TP = float(r.split("True peak:")[1].split("Peak:")[1].split("dBFS")[0])
    return I, TP

NIV = dict(mus_db=float(os.environ.get("MUS_DB", -7)), amb_db=float(os.environ.get("AMB_DB", 0)), fx_db=float(os.environ.get("FX_DB", -4)))
mezcla(f"{T}/mezcla_pre.wav", **NIV)
I, TP = lufs(f"{T}/mezcla_pre.wav"); gan = -14.0 - I
mezcla(f"{T}/mezcla.wav", gan=gan, limite=10 ** (-1.5 / 20), **NIV)
I2, TP2 = lufs(f"{T}/mezcla.wav"); print(f"Mezcla: {I:.1f} → {I2:.1f} LUFS, pico verdadero {TP2:.1f} dBTP (ganancia {gan:+.1f} dB)")
if os.environ.get("MEDIR"):                       # voz contra fondo, frase por frase (el fondo sigue bajando con la voz)
    mezcla(f"{T}/solo_voz.wav", mus_db=-120, amb_db=-120, fx_db=-120, gan=gan)
    mezcla(f"{T}/solo_fondo.wav", voz_oir=-120, gan=gan, **NIV)
    for i in range(1, 9):
        a = t[f"L{i}"]; b = a + V[f"L{i}"]
        def rms(p):
            r = subprocess.run(["ffmpeg", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", p, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
            return float(r.split("mean_volume:")[1].split("dB")[0])
        vz, fd = rms(f"{T}/solo_voz.wav"), rms(f"{T}/solo_fondo.wav")
        print(f"L{i}: voz {vz:6.1f} dB · fondo {fd:6.1f} dB · diferencia {vz - fd:5.1f} dB")

# ---------- imagen + textos + audio ----------
if SOLO_AUDIO: sys.exit(0)
ins = []
for f in lista: ins += ["-i", f]
n = len(lista)
fv = (''.join(f'[{i}:v]' for i in range(n)) + f"concat=n={n}:v=1:a=0,setsar=1,format=yuv444p[base];"
      f"[{n}:v]scale=out_color_matrix=bt709:out_range=tv,format=yuva444p[tx];"
      f"[base][tx]overlay=0:0:format=yuv444:eof_action=pass,format=yuv420p[v]")
cmd = ["ffmpeg", "-v", "error", "-n"] + ins + ["-framerate", "30", "-i", f"{T}/textos/%04d.png", "-i", f"{T}/mezcla.wav",
       "-filter_complex", fv, "-map", "[v]", "-map", f"{n + 1}:a", "-t", f"{FIN:.3f}",
       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30",
       "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-map_metadata", "-1", "-movflags", "+faststart", salida]
subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)
print("Exportado:", salida)
