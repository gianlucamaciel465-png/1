# Montaje de ROCCE_lo_que_te_frena_v02: la línea de tiempo se calcula con la duración de cada frase de la locución,
# así que cambiar la voz guía por la grabación de Gianluca es volver a correr esto con otra carpeta de frases.
#
# Historia: el villano (lo que nos hace postergar) → el protagonista se suelta (animación de v01, conservada) →
# Gianluca, de verdad, haciendo las fotos de sus remeras junto al mar ("Fracasé. Me incomodé. Y acá estoy.") →
# la acción vuelve al espectador ("Ahora te toca a vos." + el plan) → placa con una sola acción.
#
#   A  animación (TRABAJO/frena2/anim, 7,10 s) ............ música de R1: tensión (tirones) y liberación (soga, llegada)
#   B1 IMG_7887 desde 0,00 (rompe una ola; Gianluca saca la foto) ..... "Fracasé." "Me incomodé."   colchón suave
#   B2 IMG_7884 desde 2,90 (por encima de su hombro, la blanca) ....... "Y acá estoy."
#   C1 IMG_7857 desde 2,90 (la blanca puesta, de espaldas, frente al mar) "Ahora te toca a vos." "El primero de…"
#   C2 IMG_7824 desde 4,20 (la negra viene hacia cámara) .............. "…y creá lo que viene con nosotros."
#   D  IMG_7896 (placa de la casa, acercándose) ........................ "Mandanos FOUNDERS y pedí acceso."
#      textos aprobados: "Drop Founders Privée —" · "01/11/2026" · "Sé uno de los primeros 100." + ruta.
# Música: R1 (Neuron Visuals) en tres usos: tal cual en A; solo su capa melódica (separada con demucs), filtrada y
# baja bajo la confesión; y su subida otra vez desde el principio en C ("ahora te toca a vos") de modo que su golpe de
# llegada (5,50 s del original) caiga justo en el corte a la placa. Efectos propios (scripts/sfx.py): subida y golpe en
# la entrada de C, golpe en la placa. La música baja sola cuando habla la voz (sidechain).
#
# Uso: python3 montaje_v02.py VOZ_DIR SALIDA.mp4
#   VOZ_DIR/p1.wav … p6.wav = las seis frases ya recortadas (sin silencio adelante ni atrás):
#   p1 "Fracasé."  p2 "Me incomodé."  p3 "Y acá estoy."  p4 "Ahora te toca a vos."
#   p5 "El primero de noviembre, hacete founder de Roccé y creá lo que viene con nosotros."  p6 "Mandanos FOUNDERS y pedí acceso."
#   Variables: GAN (dB final), VOZ_DB (ganancia de la voz), CORTE_P5 (fracción de p5 donde entra la negra, 0,55).
import os, sys, json, subprocess

voz_dir, salida = sys.argv[1], sys.argv[2]
R = "/home/user/1" if os.path.isdir("/home/user/1") else os.getcwd()
os.chdir(R)
T = "TRABAJO/frena2"; C = f"{T}/clips"; os.makedirs(C, exist_ok=True)
R1 = "REFERENCIAS/REF_15_neuronvisuals_soga_DeUC8-gxNIn.mp4"
STEMS = os.environ.get("STEMS", "TRABAJO/frena/stems")          # other.wav y bass.wav de R1 (demucs)
FPS = 30

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode())
def q(t): return round(round(t * FPS) / FPS, 4)          # a cuadro exacto

v = [dur(os.path.join(voz_dir, f"p{i}.wav")) for i in range(1, 7)]
# ---------- línea de tiempo ----------
A_END = 213 / FPS                                        # 7,10
t = {}
B0 = A_END
t["p1"] = B0 + 0.45                                       # después del golpe de la ola
t["p2"] = t["p1"] + v[0] + 0.40
B2 = q(t["p2"] + v[1] + 0.20)                             # corte a la blanca por encima del hombro
t["p3"] = B2 + 0.25
C0 = q(t["p3"] + v[2] + 0.45)                             # "Ahora te toca a vos": vuelve la energía
t["p4"] = C0 + 0.12
t["p5"] = t["p4"] + v[3] + 0.30
# la negra entra en "creá" si la preparación de la voz guardó las palabras; si no, a una fracción de la frase
corte_p5 = v[4] * float(os.environ.get("CORTE_P5", 0.55))
try:
    prep = json.load(open(os.path.join(voz_dir, "preparacion.json")))
    for w, ws, we in prep["frases"][4]["palabras"]:
        if w.lower().strip(",.").startswith("cre"): corte_p5 = max(0.0, ws - 0.04); break
except (OSError, KeyError, IndexError, ValueError):
    pass
C2 = q(t["p5"] + corte_p5)
D0 = q(t["p5"] + v[4] + 0.30)                             # placa sobre el golpe de llegada de la música
t["p6"] = D0 + 0.60
FIN = q(t["p6"] + v[5] + 2.60)                            # tiempo para leer la placa después de la voz
segs = [("A", 0, A_END), ("B1", B0, B2), ("B2", B2, C0), ("C1", C0, C2), ("C2", C2, D0), ("D", D0, FIN)]
lin = {"voz": dict(zip(["p1", "p2", "p3", "p4", "p5", "p6"], v)), "inicio_frases": t,
       "cortes": {k: (round(a, 3), round(b, 3)) for k, a, b in segs}, "duracion": FIN}
json.dump(lin, open(f"{T}/linea_de_tiempo.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(lin, indent=1, ensure_ascii=False))
for k, a, b in segs[1:]:
    assert b - a > 0.3, f"tramo {k} demasiado corto"

# ---------- tomas ----------
ENC = ["-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
       "-color_trc", "bt709", "-colorspace", "bt709", "-an"]
SC = "scale=1080:1920:flags=lanczos:out_range=tv,format=yuv420p,fps=30,setsar=1"
SOLO = bool(os.environ.get("AUDIO_SOLO"))
def clip(nombre, src, desde, n, vf=SC):
    if SOLO: return
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{desde:.3f}", "-i", src, "-vf", vf, "-frames:v", str(n)] + ENC + [f"{C}/{nombre}.mp4"], check=True)
nf = lambda a, b: int(round((b - a) * FPS))
if not SOLO: subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{T}/anim/%04d.png", "-vf",
                "scale=out_range=tv:out_color_matrix=bt709,format=yuv420p,setsar=1", "-frames:v", "213"] + ENC + [f"{C}/A.mp4"], check=True)
clip("B1", "ORIGINALES/IMG_7887.mov", 0.00, nf(B0, B2))
clip("B2", "ORIGINALES/IMG_7884.mov", 2.90, nf(B2, C0))
clip("C1", "ORIGINALES/IMG_7857.mov", 2.90, nf(C0, C2))
clip("C2", "ORIGINALES/IMG_7824.mov", 4.20, nf(C2, D0))
dD = FIN - D0; d_ini = max(0.3, 6.15 - dD)
clip("D", "ORIGINALES/IMG_7896.mov", d_ini, nf(D0, FIN),
     "crop=w=iw/1.16:h=ih/1.16:x=iw*0.024:y=ih*0.07,scale=1080:1920:flags=lanczos:in_range=pc:out_range=tv,format=yuv420p,fps=30,setsar=1")
for k, a, b in ([] if SOLO else segs[1:]):
    n = int(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                                      "stream=nb_read_frames", "-of", "csv=p=0", f"{C}/{k}.mp4"]).decode())
    assert n == nf(a, b), f"{k}: {n} cuadros (esperados {nf(a, b)}): la toma no alcanza"

# ---------- efectos ----------
cues = [{"tipo": "subida", "t": C0, "dur": 0.75, "db": -17}, {"tipo": "golpe", "t": C0, "db": -9},
        {"tipo": "golpe", "t": D0, "db": -8}]
json.dump(cues, open(f"{T}/cues.json", "w"))
subprocess.run(["python3", "scripts/sfx.py", f"{T}/fx.wav", f"{FIN:.3f}", f"{T}/cues.json"], check=True)

# ---------- montaje ----------
X = "TRABAJO/frena/textos"; X2 = f"{T}/textos"
ms = lambda s: int(round(s * 1000))
ins = ["-i", f"{C}/A.mp4", "-i", f"{C}/B1.mp4", "-i", f"{C}/B2.mp4", "-i", f"{C}/C1.mp4", "-i", f"{C}/C2.mp4", "-i", f"{C}/D.mp4"]
for png in (f"{X2}/placa_fondo2.png", f"{X}/placa1.png", f"{X}/placa2.png", f"{X}/placa3.png", f"{X2}/ruta.png"):
    ins += ["-framerate", "30", "-loop", "1", "-t", f"{FIN:.3f}", "-i", png]
ins += ["-i", R1, "-i", f"{STEMS}/other.wav", "-i", f"{STEMS}/bass.wav"]                               # 11, 12, 13
for i in range(1, 7): ins += ["-i", os.path.join(voz_dir, f"p{i}.wav")]                              # 14–19
ins += ["-i", "ORIGINALES/IMG_7887.mov", "-i", "ORIGINALES/IMG_7884.mov", "-i", "ORIGINALES/IMG_7857.mov",
        "-i", "ORIGINALES/IMG_7896.mov", "-i", f"{T}/fx.wav"]                                         # 20–24
def ov(i, st, name, d=0.15): return f"[{i}:v]format=rgba,fade=t=in:st={st:.3f}:d={d}:alpha=1[{name}]"
P_ON, R_ON = D0 + 0.30, t["p6"]
AF = "aresample=48000,aformat=channel_layouts=stereo"
# R1 otra vez en C: su golpe de llegada (5,50) cae en D0
s0 = 5.50 - (D0 - C0); pre = 0.0
if s0 < 0.0: pre, s0 = -s0, 0.0
largo_B = C0 - B0 + pre
VOZ_DB = float(os.environ.get("VOZ_DB", 8))
voces = ";".join(f"[{13 + i}:a]{AF},highpass=f=90,acompressor=threshold=0.08:ratio=3:attack=5:release=120:makeup=1.6,"
                 f"volume={VOZ_DB}dB,adelay={ms(t[f'p{i}'])}|{ms(t[f'p{i}'])}[v{i}]" for i in range(1, 7))
MUS_DB, AMB_DB = os.environ.get("MUS_DB", "0"), os.environ.get("AMB_DB", "0")
fv = f"""
[0:v][1:v][2:v][3:v][4:v][5:v]concat=n=6:v=1:a=0,setsar=1,format=yuv420p[base];
{ov(6, D0, 'g', 0.2)};{ov(7, D0 + 0.05, 'c1')};{ov(8, D0 + 0.15, 'c2')};{ov(9, P_ON, 'c3', 0.18)};{ov(10, R_ON, 'c4', 0.18)};
[base][g]overlay=0:0:enable='gte(t,{D0:.3f})'[v1];[v1][c1]overlay=0:0:enable='gte(t,{D0:.3f})'[v2];
[v2][c2]overlay=0:0:enable='gte(t,{D0:.3f})'[v3];[v3][c3]overlay=0:0:enable='gte(t,{P_ON:.3f})'[v4];
[v4][c4]overlay=0:0:enable='gte(t,{R_ON:.3f})',format=yuv420p[v]
"""
fc = f"""
[11:a]{AF},atrim=0.20:7.42,asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st=6.95:d=0.27[mA];
[12:a]{AF},atrim=0:{largo_B + 0.5:.3f},asetpts=PTS-STARTPTS,lowpass=f=1500,volume=-8dB,afade=t=in:d=0.5,afade=t=out:st={largo_B - 0.1:.3f}:d=0.45,adelay={ms(B0 - 0.05)}|{ms(B0 - 0.05)}[mB];
[11:a]{AF},atrim={s0:.3f}:5.50,asetpts=PTS-STARTPTS,afade=t=in:d=0.06,adelay={ms(C0 + pre)}|{ms(C0 + pre)}[mC];
[11:a]{AF},atrim=5.50:8.04,asetpts=PTS-STARTPTS,volume=-3dB,afade=t=out:st=2.3:d=0.24,adelay={ms(D0)}|{ms(D0)}[mD];
[12:a]{AF},atrim=6.0:{6.0 + max(0.8, FIN - D0 - 2.2):.3f},asetpts=PTS-STARTPTS[o2];[13:a]{AF},atrim=6.0:{6.0 + max(0.8, FIN - D0 - 2.2):.3f},asetpts=PTS-STARTPTS[b2];
[o2][b2]amix=inputs=2:normalize=0,volume=7dB,afade=t=in:d=0.3,afade=t=out:st={max(0.3, FIN - D0 - 2.2 - 0.8):.3f}:d=0.8,adelay={ms(D0 + 2.2)}|{ms(D0 + 2.2)}[mE];
[mA][mB][mC][mD][mE]amix=inputs=5:normalize=0:duration=longest[mus];
{voces};
[v1][v2][v3][v4][v5][v6]amix=inputs=6:normalize=0:duration=longest,asplit=2[voz0][sc];[voz0]volume={os.environ.get("VOZ_OIR", "0")}dB[voz];
[mus][sc]sidechaincompress=threshold=0.03:ratio=4:attack=15:release=300:makeup=1,volume={MUS_DB}dB[musd];
[20:a]{AF},atrim=0:{B2 - B0 + 0.3:.3f},asetpts=PTS-STARTPTS,volume='if(lt(t,0.40),1.25,0.40)':eval=frame,afade=t=out:st={B2 - B0 - 0.1:.3f}:d=0.4,adelay={ms(B0)}|{ms(B0)}[e1];
[21:a]{AF},atrim=2.9:{2.9 + C0 - B2 + 0.2:.3f},asetpts=PTS-STARTPTS,volume=-6dB,afade=t=in:d=0.1,afade=t=out:st={C0 - B2 - 0.1:.3f}:d=0.3,adelay={ms(B2)}|{ms(B2)}[e2];
[22:a]{AF},atrim=2.9:{2.9 + C2 - C0:.3f},asetpts=PTS-STARTPTS,volume=-12dB,afade=t=in:d=0.2,afade=t=out:st={C2 - C0 - 0.3:.3f}:d=0.3,adelay={ms(C0)}|{ms(C0)}[e3];
[23:a]{AF},atrim={d_ini:.3f}:{d_ini + FIN - D0:.3f},asetpts=PTS-STARTPTS,volume=8dB,afade=t=in:d=0.2,afade=t=out:st={FIN - D0 - 0.5:.3f}:d=0.5,adelay={ms(D0)}|{ms(D0)}[e4];
[24:a]{AF}[fx];
[e1][e2][e3][e4]amix=inputs=4:normalize=0:duration=longest,volume={AMB_DB}dB[amb];
[musd][voz][amb][fx]amix=inputs=4:normalize=0:duration=longest,atrim=0:{FIN:.3f},volume={os.environ.get('GAN', '0')}dB,alimiter=limit={os.environ.get('LIM', '0.76')}:level=false[au]
"""
if os.environ.get("AUDIO_SOLO"):          # solo la mezcla (para medir voz contra fondo): MUS_DB/AMB_DB=-90 apagan capas; VOZ_OIR=-90 apaga la voz sin sacar el ducking
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", fc.strip(), "-map", "[au]", "-t", f"{FIN:.3f}", "-c:a", "pcm_s16le", salida], check=True)
    print("Audio:", salida); sys.exit(0)
cmd = ["ffmpeg", "-v", "error", "-stats", "-n"] + ins + ["-filter_complex", (fv + ";" + fc).replace("\n;", ";"), "-map", "[v]", "-map", "[au]", "-t", f"{FIN:.3f}",
       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30",
       "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", salida]
subprocess.run(cmd, check=True)
print("Exportado:", salida)
