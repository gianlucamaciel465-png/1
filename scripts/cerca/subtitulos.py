# Subtítulos de "ESTUVISTE CERCA" (.ass para libass): blancos, Inter Display SemiBold, sombra suave, hasta 2 líneas,
# por encima de la interfaz de Reels (borde inferior del bloque a 1400 px de 1920). Tiempos = voz real (linea.py).
# Uso: python subtitulos.py VOZ_DIR SALIDA.ass
import sys, soundfile as sf
sys.path.insert(0, __file__.rsplit("/", 1)[0]); from linea import VOZ
vd, out = sys.argv[1:3]
d = {k: sf.info(f"{vd}/{k}.wav").duration for k in VOZ}
S = [  # (texto, frase de inicio, frase de fin)  \N = salto de línea
 ("Abue, hace un año\\Nque no me sale una.", "c1", "c1"), ("¿Qué pasó?", "a1", "a1"),
 ("Antes me sacaba nueves\\Ny jugaba de titular.", "c2a", "c2a"), ("Ahora estudio el doble\\Ny desapruebo igual.", "c2b", "c2b"),
 ("El domingo entré\\Ncinco minutos.", "c2c", "c2c"), ("La única que tuve…", "c2d", "c2d"), ("…pegó en el palo.", "c2e", "c2e"),
 ("Seguí yendo, mi amor.", "a2", "a2"), ("Eso hago, abue.", "c3a", "c3a"), ("Estoy cansado.", "c3b", "c3b"),
 ("Ya siento que no sirvo\\Npara nada.", "c3c", "c3c"), ("¿Estuviste cerca\\Nentonces, muchacho?", "a3", "a3"), ("Sí.", "c4", "c4"),
 ("Acá también lo estuvieron.", "a4a", "a4a"), ("Seguí para adelante.", "a4b", "a4b"),
]
def ts(t): h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60; return f"{h}:{m:02d}:{s:05.2f}"
L = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "",
     "[V4+ Styles]",
     "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
     "Style: Sub,Inter Display SemiBold,60,&H00FFFFFF,&H00FFFFFF,&H90000000,&HA0000000,0,0,0,0,100,100,0.5,0,1,1.6,2.2,2,110,110,520,1", "",
     "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
prev_end = 0
for i, (txt, a, b) in enumerate(S):
    t0 = VOZ[a] - 0.08; t1 = VOZ[b] + d[b] + 0.25
    if i + 1 < len(S): t1 = min(t1, VOZ[S[i + 1][1]] - 0.10)
    t1 = max(t1, t0 + 0.7)
    L.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},Sub,,0,0,0,,{{\\blur1.2\\fad(80,80)}}{txt}")
open(out, "w").write("\n".join(L) + "\n"); print(len(S), "subtítulos")
