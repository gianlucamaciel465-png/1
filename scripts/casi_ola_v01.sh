#!/usr/bin/env bash
# ROCCE_casi_ola_v01 — concepto "casi impacto" (R5 globo / R7 lata, la de mejor resultado) con material real:
# una ola real avanza hacia las dos remeras en las rocas, un contador "FRAMES TO IMPACT" baja y se frena,
# la imagen se congela a milímetros del impacto con "so f★cking close." → la frase hecha prenda (macro del
# pecho) → espalda blanca → negra puesta → placa con ambas remeras y "Drop Founders Privée — 01/11/2026".
# Audio: sonido real de las tomas (ola de IMG_4631, mar de IMG_7896) + tics sintetizados del contador.
# Sin música (no hay pista con uso permitido en el repo); sin voz; sin subtítulos.
#
# Montaje (30 fps, 315 cuadros = 10,5 s):
#   H  0,000–4,300  IMG_4631 (HDR) 0,70–3,87 s en movimiento (96 cuadros) + congelado del cuadro de 3,867 s (33)
#                   contador 120→001 (n = 1 + ceil(119·(1−t/T)^2,2), T = 3,1667 s), rojo desde 1,727 s (n ≤ 22).
#   P1 4,300–5,600  IMG_3375 (HDR) 0,55–1,85: mano con el frente de la blanca, "so f★cking close." estampado.
#   P2 5,600–7,100  IMG_4530 (HDR) 0,80–2,30: espalda blanca sostenida, ROCCÉ en denim + Founders Privée.
#   P3 7,100–8,500  IMG_7793 2,60–4,00: negra puesta de espaldas, estampado completo.
#   Z  8,500–10,500 IMG_7896 4,15–6,15 acercada 1,16× (ambas remeras completas) + cierre en dos líneas.
# Uso: scripts/casi_ola_v01.sh [SALIDA]
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-EXPORTACIONES/ROCCE_casi_ola_v01.mp4}"
[ -e "$OUT" ] && { echo "ERROR: $OUT ya existe"; exit 1; }
T=TRABAJO/casi; C=$T/clips; X=$T/textos; mkdir -p $C $X
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
ENC="-c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -an"
F=/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf

# 1) tomas
ffmpeg -v error -y -ss 0.70 -i ORIGINALES/IMG_4631.mov -vf "$TM,fps=30,scale=1080:1920:flags=lanczos,setsar=1" -frames:v 96 $ENC $C/H_4631.mp4
ffmpeg -v error -y -ss 0.55 -i ORIGINALES/IMG_3375.mov -vf "$TM,fps=30,scale=1080:1920:flags=lanczos,setsar=1" -frames:v 39 $ENC $C/P1_3375.mp4
ffmpeg -v error -y -ss 0.80 -i ORIGINALES/IMG_4530.mov -vf "$TM,fps=30,scale=1080:1920:flags=lanczos,setsar=1" -frames:v 45 $ENC $C/P2_4530.mp4
ffmpeg -v error -y -ss 2.60 -i ORIGINALES/IMG_7793.mov -vf "scale=1080:1920:flags=lanczos:out_range=tv,format=yuv420p,fps=30,setsar=1" -frames:v 42 $ENC $C/P3_7793.mp4
ffmpeg -v error -y -ss 4.15 -i ORIGINALES/IMG_7896.mov -vf "crop=w=iw/1.16:h=ih/1.16:x=iw*0.024:y=ih*0.07,scale=1080:1920:flags=lanczos:in_range=pc:out_range=tv,format=yuv420p,fps=30,setsar=1" -frames:v 60 $ENC $C/Z_7896.mp4

# 2) textos (exactos) y tics
SOMBRA=#FFFFFF python3 scripts/texto_png.py $X/etiqueta.png 34 292 "FRAMES TO IMPACT|#111111"
SOMBRA=#FFFFFF python3 scripts/texto_png.py $X/frase.png 68 650 "so f★cking close.|#111111"
python3 scripts/texto_png.py $X/cierre1.png 56 330 "Drop Founders Privée —|#FFFFFF"
python3 scripts/texto_png.py $X/cierre2.png 124 460 "01/11/2026|#FFFFFF"
python3 scripts/tics_contador.py $T/tics.wav 120 3.16667 2.2

# 3) contador: tres celdas de dígitos (cifras tabulares), negro y luego rojo
N="if(gte(t\,3.16667)\,1\,1+ceil(119*pow(1-t/3.16667\,2.2)))"
cnt=""
for col in "0x111111:lt(t\,1.727)" "0xD7261E:between(t\,1.727\,4.3)"; do
  c=${col%%:*}; en=${col#*:}
  i=0
  for dig in "floor(($N)/100)" "mod(floor(($N)/10)\,10)" "mod($N\,10)"; do
    x=$((408 + 132 * i)); i=$((i + 1))
    cnt="$cnt,drawtext=fontfile=$F:text='%{eif\:$dig\:d}':fontsize=200:fontcolor=$c:x=$x-text_w/2:y=330:enable='$en'"
  done
done

# 4) montaje
ffmpeg -v error -stats -n \
  -i $C/H_4631.mp4 -i $C/P1_3375.mp4 -i $C/P2_4530.mp4 -i $C/P3_7793.mp4 -i $C/Z_7896.mp4 \
  -framerate 30 -loop 1 -t 4.3 -i $X/etiqueta.png \
  -framerate 30 -loop 1 -t 4.3 -i $X/frase.png \
  -framerate 30 -loop 1 -t 2.0 -i $X/cierre1.png \
  -framerate 30 -loop 1 -t 2.0 -i $X/cierre2.png \
  -i ORIGINALES/IMG_4631.mov -i ORIGINALES/IMG_7896.mov -i $T/tics.wav \
  -filter_complex "
  [0:v]tpad=stop_mode=clone:stop=33,setpts=PTS-STARTPTS,format=yuv420p[h0];
  [h0][5:v]overlay=0:0:shortest=1[h1];
  [6:v]format=rgba,fade=t=in:st=3.40:d=0.12:alpha=1[fr];
  [h1][fr]overlay=0:0:shortest=1$cnt,format=yuv420p[h];
  [1:v]colorchannelmixer=rr=0.945:gg=1.065:bb=1.165,setpts=PTS-STARTPTS,format=yuv420p[p1];
  [2:v]colorchannelmixer=rr=1.05:gg=1.03:bb=0.92,setpts=PTS-STARTPTS,format=yuv420p[p2];
  [3:v]setpts=PTS-STARTPTS,format=yuv420p[p3];
  [4:v]geq=lum='lum(X,Y)*(1-0.55*max(0,1-Y/900))':cb='cb(X,Y)':cr='cr(X,Y)',setpts=PTS-STARTPTS[z0];
  [7:v]format=rgba,fade=t=in:st=0.12:d=0.15:alpha=1[c1];
  [8:v]format=rgba,fade=t=in:st=0.30:d=0.15:alpha=1[c2];
  [z0][c1]overlay=0:0:shortest=1[z1];[z1][c2]overlay=0:0:shortest=1,format=yuv420p[z];
  [h][p1][p2][p3][z]concat=n=5:v=1:a=0,setsar=1,format=yuv420p[v];
  [9:a]aresample=48000,asplit=3[w1][w2][w3];
  [w1]atrim=0.70:3.8667,asetpts=PTS-STARTPTS,afade=t=out:st=3.117:d=0.05[ola];
  [w2]atrim=3.8667:5.0,asetpts=PTS-STARTPTS,lowpass=f=450,volume=-20dB,afade=t=in:d=0.05,afade=t=out:st=1.08:d=0.05,adelay=3167|3167[susp];
  [w3]atrim=3.55:6.40,asetpts=PTS-STARTPTS,afade=t=out:st=2.05:d=0.8,adelay=4300|4300[golpe];
  [10:a]aresample=48000,atrim=2.35:6.15,asetpts=PTS-STARTPTS,volume=8dB,afade=t=in:d=0.6,afade=t=out:st=3.3:d=0.5,adelay=6700|6700[mar];
  [11:a]aresample=48000,aformat=channel_layouts=stereo[tic];
  [ola][susp][golpe][mar][tic]amix=inputs=5:normalize=0:duration=longest,atrim=0:10.5,volume=${GAN:-2}dB,alimiter=limit=0.84:level=false,aformat=channel_layouts=stereo[au]" \
  -map "[v]" -map "[au]" -t 10.5 \
  -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -r 30 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
echo "Exportado: $OUT"
