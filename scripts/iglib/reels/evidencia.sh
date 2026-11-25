#!/bin/bash
# Evidencia de un máster IGLIB: decodificación completa, ffprobe resumido, md5 de video y audio, sonoridad (ebur128),
# hoja de contacto cada 0,5 s, cuadros a resolución completa (c0, cada corte y el giro), miniaturas a 360 px (c0 y CTA).
# Uso: evidencia.sh MP4 SALIDA_DIR PREFIJO "cortes(cuadros separados por espacio)" GIRO CTA
set -uo pipefail
F="$1"; O="$2"; P="$3"; CORTES="$4"; GIRO="$5"; CTA="$6"; mkdir -p "$O"
PYE=/home/user/1/TRABAJO/iglib/env/bin/python
echo "== $P · $(basename "$F")"
echo -n "decodificación completa: "; e=$(ffmpeg -v error -i "$F" -f null - 2>&1); [ -z "$e" ] && echo "OK, sin errores" || echo "$e"
ffprobe -v error -show_entries format=duration,size,bit_rate:stream=index,codec_type,codec_name,profile,level,width,height,pix_fmt,r_frame_rate,nb_frames,duration,color_space,color_transfer,color_primaries,color_range,sample_rate,channels -of compact "$F"
echo -n "metadatos de formato (tags): "; ffprobe -v error -show_entries format_tags -of compact=nk=0 "$F" | tr '\n' ' '; echo
echo -n "md5 video: "; ffmpeg -v error -i "$F" -map 0:v -f md5 - ; echo -n "md5 audio: "; ffmpeg -v error -i "$F" -map 0:a -f md5 -
echo -n "md5 archivo: "; md5sum "$F" | cut -d' ' -f1
ffmpeg -nostats -i "$F" -vn -af ebur128=peak=true:framelog=quiet -f null - 2>&1 | grep -E "^\s+(I|LRA|Peak):" | tr -s ' '
# hoja de contacto cada 0,5 s (cuadro, tiempo)
ffmpeg -v error -y -i "$F" -vf "select='not(mod(n\,15))',scale=270:480,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='c%{n} %{pts\:hms}':x=6:y=6:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=8x6" -fps_mode passthrough "$O/${P}_contacto_0-5s_%02d.jpg"
# el filtro tile numera los cuadros elegidos; se rehace el texto con el cuadro real
rm -f "$O/${P}_contacto_0-5s_"*.jpg
$PYE - "$F" "$O" "$P" <<'PY'
import sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
F, O, P = sys.argv[1:4]
raw = subprocess.run(['ffmpeg','-v','error','-i',F,'-vf',"select='not(mod(n\\,15))',scale=270:480:flags=area",'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
fr = np.frombuffer(raw,np.uint8).reshape(-1,480,270,3); font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 17)
cols = 8; rows = (len(fr)+cols-1)//cols; im = Image.new('RGB',(270*cols,480*rows),(20,20,20)); d = ImageDraw.Draw(im)
for i,f in enumerate(fr):
    x,y = (i%cols)*270,(i//cols)*480; im.paste(Image.fromarray(f),(x,y)); n=i*15
    d.rectangle([x,y,x+150,y+24],fill=(0,0,0)); d.text((x+5,y+3),f'c{n} · {n/30:.2f}s',fill=(255,230,0),font=font)
im.save(f'{O}/{P}_contacto_cada_0-5s.jpg',quality=88); print('hoja de contacto:', f'{O}/{P}_contacto_cada_0-5s.jpg', len(fr), 'cuadros')
PY
cuadro() { ffmpeg -v error -y -i "$F" -vf "select='eq(n\,$1)'" -fps_mode passthrough -frames:v 1 "$2"; }
cuadro 0 "$O/${P}_c0000_completo.png"
for c in $CORTES; do cuadro $c "$O/${P}_corte_c$(printf %04d $c).png"; done
cuadro $GIRO "$O/${P}_giro_c$(printf %04d $GIRO).png"
ffmpeg -v error -y -i "$F" -vf "select='eq(n\,0)',scale=360:640:flags=area" -fps_mode passthrough -frames:v 1 "$O/${P}_c0000_360px.png"
ffmpeg -v error -y -i "$F" -vf "select='eq(n\,$CTA)',scale=360:640:flags=area" -fps_mode passthrough -frames:v 1 "$O/${P}_cta_c$(printf %04d $CTA)_360px.png"
echo "cuadros guardados en $O"
