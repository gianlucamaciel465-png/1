"""Hoja de máster v01 de MC-01 y MC-02 (Pedro A) a partir de la evidencia medida (control.json, planos.json,
audio.json, entrega.json). Uso: python hoja_mc0102.py mc01|mc02 → escribe 01_pedro_hoja_master_v01.md en la carpeta de
la pieza. Los números salen de los JSON; el texto fijo (guion, desvíos, personas) está acá, revisado a mano."""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mc0102_util as M          # noqa: E402

U = M.U
REGLA = ('REGLA PERMANENTE · CASA DE APUESTAS (textual): «Todo contenido de Roccé usa la mecánica de retención de una '
         'casa de apuestas. Es mecánica, no estética ni promoción de apuestas: una apuesta abierta desde el primer '
         'segundo, evidencia a favor y en contra a toda velocidad, y la resolución lo más tarde posible.»')


def s(c):
    return f'{c / 30:.3f}'.replace('.', ',')


def num(x, d=1):
    return ('—' if x is None else f'{x:+.{d}f}').replace('.', ',')


def fuente_s(toma, n):
    try:
        return U.tiempos_src(toma)[n] if toma not in U._PTS else U._PTS[toma][n]
    except Exception:
        return None


def tramo_fuente(p):
    toma = p['toma']
    a = p['n0']; b = p['n0'] + (p.get('n_src') or p['cuadros']) - 1
    try:
        pts = U.tiempos_src(toma)
        ta, tb = pts[int(a)], pts[int(b)]
        return f'{int(a)}–{int(b)} ({ta:.3f}–{tb:.3f} s)'.replace('.', ',')
    except Exception:
        return f'{int(a)}–{int(b)}'


def tabla(filas, cab):
    out = ['| ' + ' | '.join(cab) + ' |', '|' + '---|' * len(cab)]
    out += ['| ' + ' | '.join(str(x) for x in f) + ' |' for f in filas]
    return '\n'.join(out)


# ---------------------------------------------------------------------------------------------------------------------
PIEZAS = {
    'mc01': dict(
        T=Path('/home/user/1/TRABAJO/marca/MC-01'), titulo='MC-01 · «LADRILLO A LADRILLO · Cap. 1»',
        pieza=Path('/mnt/project-files/piezas/MARCA_comunidad/MC-01_ladrillo_a_ladrillo'),
        sonido_fuera=('Las ráfagas de 7887 (fuente 1,45–1,60 y 2,88–3,05 s; máster 1,45–1,60 y 2,98–3,15 s) van atenuadas '
                      '12 dB. 4531 no se usa en esta pieza. El VAR (c255–c299) va sin ambiente, como pide el guion.'),
        silencios=('ninguna en A ni en B. En _SINMUSICA: 4,2–4,6 s (plano 5: 3453 no tiene audio útil y solo quedan el '
                   'foley de tela de 3,85 s y el tic de 4,0 s) y 8,5–9,9 s (VAR: el guion lo pide sin ambiente y, sin música, '
                   'solo quedan los bips de 8,6 s). El final no tiene silencio.'),
        receta='scripts/marca/mc01.py (+ mc0102_util.py)', nf=462,
        guion={'01': 'c0–c35 · 7887 0,00–1,20 · completo', '02': 'c36–c59 · 7887 1,20–2,00 · z 1,25, cx≈1500, cy≈1740',
               '03': 'c60–c83 · 8008 1,40–2,20', '04': 'c84–c113 · 7887 2,70–3,70', '05': 'c114–c140 · 3453 3,30–4,20 (HDR→SDR + TOMAS)',
               '06': 'c141–c170 · 7824 4,80–5,80', '07': 'c171–c197 · 7894 0,30–1,20', '08': 'c198–c224 · 4641 1,20–2,10',
               '09': 'c225–c254 · 4641 2,10–3,10 · z 1,00→1,08, sat 1→0,15', '10': 'c255–c299 · 7887 3,10–3,70 a vel 0,4 · s 0,35, contraste 1,08 + VAR',
               '11': 'c300–c344 · 7885 3,10–4,60', '12': 'c345–c374 · 4631 2,40–3,40', '13': 'c375–c461 · 4631 3,40–6,30'},
        desvio_plano={'02': 'cx 1500 pedido → 1296 efectivo: con z 1,25 la ventana (1728×3072) toca el borde derecho de la toma (x 432–2160, y 204–3276).',
                      '03': '8008 tiene 65 cuadros (0–64): 1,40–2,20 pediría el cuadro 66. Se usan 41–64 (1 cuadro antes).',
                      '05': 'tela oscura de la Negra neutralizada (ver Color): con la corrección de TOMAS seguía marrón.',
                      '10': '7887 termina en el cuadro 110 (3,667 s): 18 cuadros reales (93–110) estirados a 45 con mezcla lineal → vel 0,386.'},
        desvios=[
            'Plano 3: 8008 llega al cuadro 64; se usan 41–64 (1,367–2,167 s) en vez de 1,40–2,20. MC-02 usa 12–40 de la misma toma: no se repite ningún cuadro.',
            'Plano 2: el acercamiento 1,25 con cx 1500 se sale de la toma; la ventana queda contra el borde derecho (cx efectivo 1296). La cabeza queda debajo de y 700 (cuadros_A/c036.jpg, c059.jpg).',
            'Plano 10 (VAR): 18 cuadros reales (7887 93–110) a 45 cuadros con mezcla lineal de cuadros (vel 0,386, no 0,4: no hay más fuente). Ningún cuadro repetido (diferencia entre cuadros consecutivos en la tabla de control) y sin fantasmas sobre el estampado a tamaño real (var_tamano_real/).',
            'Criterio común de la tanda (25/11): los datos chicos sobre fondo claro van en caja negra 50 SemiBold (comun.caja, tema negra), con la misma y (borde superior de la caja) y el mismo cuadro de entrada: «en la fábrica de mi familia» (c84, y 570), «LA FÁBRICA: ¿EN CONTRA?» (c255, y 620) y el CTA «Seguí el marcador: Cap. 2.» (c423, y 760).',
            'La línea de y 228 («LADRILLO A LADRILLO · CAP. 1» / hook de c36–c59) sigue como dato con halo, más denso (0,75): es el rótulo del marcador, que arranca en y 300. Una caja negra de 105 px se montaría sobre el marcador, y la línea del hook A mediría 1070 px de ancho. El criterio común permite el halo en los rótulos de interfaz. Si Roma la prefiere en caja, hay que mover el marcador.',
            '«LA FÁBRICA: ¿EN CONTRA?» va en y 620, no en 570: la caja negra «REVISIÓN · VAR» (76 px) de y 460 baja hasta ≈ 599.',
            'Placas: 88 px por defecto. «MI LABURO: LADRILLOS.» va a 80, «RELIEVE EN EL PECHO.» y «ROCCÉ, EN PARALELO.» a 86 y «Y EL MAR, EN CONTRA.» a 84, porque a 88 pasaban de 940 px. Sobre espuma o cielo el halo sube a 0,75.',
            'Pop del hook A (c0–c1): la caja «¿Una marca para el mundo / desde Cañuelas?» mide 984 px a 76 px; a 118 % (1161 px) se cortaba contra los bordes del primer cuadro. El pop se limita al ancho del cuadro menos 24 px por lado: c0 y c1 a 1,049, c2 a 1,0. El hook B y los demás pops (giro, CTA) usan 118 → 109 → 100 % completos.',
            'Plano 11: «En casa se construye / de a un ladrillo.» va a 76 px (no 80) en y 448 (no 460), con interlineado 1,0. Se funde en c337–c338: desde c339 ROCCÉ sube hasta el renglón (contacto medido). En c339–c344 la espalda queda sin texto, que es la prueba de ropa.',
            'Ficha «LADRILLOS» (pastilla de 46 px): cuelga del borde inferior del marcador, debajo de la cifra de su lado. Se enciende en c90 y viaja de EN CONTRA a A FAVOR en c315–c323. El guion no fija su posición.',
            'Color · Blanca: regla común aplicada por plano en la tela lisa (L > 170, sat < 0,15). Si pasa de B−R +12, se lleva a ≤ +8 (objetivo +6), solo en los neutros claros de la tela. Detalle en la tabla.',
            'Color · Negra 3453 (plano 5): con la corrección de video.TOMAS la tela oscura daba R−B +13, marrón. Se neutralizó solo la tela oscura (L < 95, sat < 0,45), a R−B ≈ +4: la foto negra_frente_detalle_estampado.jpg da +3,8. Letras y dedos quedan intactos (negra_plano05_antes_despues.jpg).',
            'Plano 5 sin ambiente: 3453 no tiene audio útil (RMS −54,6 dBFS). Queda el foley de tela de 3,85 s.',
            'Planos 9 y 2: acercamiento real por cuadro con fmt03.plano_z, equivalente al plano_zoom de fmt04.',
            '_SINMUSICA: ambiente, foley y tics del marcador, que son interfaz. Para llegar a −14 LUFS sin limitar fuerte lleva un compresor antes del limitador (umbral 0,03, ratio 3) y fx a −3 dB.',
        ],
        personas=['7887 (planos 1, 2, 4 y VAR): según el guion es Gianluca, de espaldas o de perfil, sin cara de frente. Que lo confirme él.',
                  '7885 (plano 11, «el chico» sentado de espaldas con la Negra): ¿Gianluca? (condición 7 de Roma). El brazo no deja ver la cara entre c300 y c344 (cuadros_A).',
                  '7824 (plano 6): manos y antebrazos sosteniendo la Negra. Pendiente quién es (antebrazos tatuados, condición 7).'],
        frases=['Nombre de la serie «LADRILLO A LADRILLO» y tema del Cap. 2 («Seguí el marcador: Cap. 2.»).',
                '«En casa se construye de a un ladrillo. Roccé también.» (OK de Gianluca, condición 8).',
                'Frase del VAR «LA FÁBRICA: ¿EN CONTRA?» (riesgo listado por Fede).',
                '«Y EL MAR, EN CONTRA.» es humor, no un dato.'],
    ),
    'mc02': dict(
        T=Path('/home/user/1/TRABAJO/marca/MC-02'), titulo='MC-02 · Respuesta a «me comí alto anuncio»',
        pieza=Path('/mnt/project-files/piezas/MARCA_comunidad/MC-02_alto_anuncio'),
        sonido_fuera=('4531 entra recién desde su segundo 3,50 (lo anterior, 0,0–3,4 s, queda fuera). El tramo de 7887 '
                      '(2,00–2,60 s) no tiene ráfagas.'),
        silencios=('ninguna en A. En _SINMUSICA, solo la última ventana (16,4–16,5 s): el ambiente de 4531 cierra con un '
                   'fundido de 0,5 s. Es menos de 0,5 s de silencio. El tecleo de c288–c323 va sin música, como pide el '
                   'guion (en A, −37,6 dBFS RMS en 9,6–10,8 s).'),
        receta='scripts/marca/mc02.py (+ mc0102_util.py)', nf=495,
        guion={'01': 'c0–c53 · 7824 0,00–1,80', '02': 'c54–c71 · 7887 2,00–2,60', '03': 'c72–c107 · 8008 0,20–1,40',
               '04': 'c108–c143 · 7999 1,50–2,70', '05': 'c144–c179 · 8002 0,00–1,20', '06': 'c180–c215 · 7884 1,00–2,20',
               '07': 'c216–c251 · 4530 1,50–2,70 (HDR)', '08': 'c252–c287 · 4625 0,40–1,60 (HDR)',
               '09': 'c288–c323 · 4625 1,60–2,80 · z 1,00→1,10', '10': 'c324–c377 · 7885 1,00–2,80',
               '11': 'c378–c494 · 4531 3,50–7,40 (audio solo desde 3,50)'},
        desvio_plano={'03': 'rampa: 12–18 a 1,0 · 18→27 a 0,5625 (16 cuadros interpolados con compensación de movimiento) · 28–40 a 1,0.',
                      '09': 'acercamiento real 1,00→1,10 centrado en el estampado (x 480, y 900).'},
        desvios=[
            'Burbuja compacta: comun.burbuja mide 181 px de alto y el guion la pide en y 236–350. Se dibuja con el estilo de comun.burbuja (radio 28, sombra, SemiBold 52 #141414, rótulo Medium gris) y el alto ajustado a la tinta: tarjeta en y 236–348. Sin usuario ni foto, en los 495 cuadros (control: burbuja_en_todos_los_cuadros).',
            'Plano 3 (8008): el guion pide 0,20–1,40; se usan los cuadros 12–40 (0,400–1,333 s) con rampa. En los cuadros 5–11 la R de ROCCÉ pasa por debajo del medidor (y 365–415) y de la burbuja, y quedaba interfaz sobre el estampado en c72–c77. Desde el cuadro 12 la R ya está debajo de y 435. Los 6 cuadros que faltan se ganan con el tramo 18→27 a 0,5625. Se probó primero la mezcla lineal y se descartó: dejaba letras dobles en ROCCÉ en c84–c89, porque la cámara se mueve 20–40 px por cuadro. Los 16 cuadros intermedios salen de minterpolate con compensación de movimiento (mi_mode=mci); los enteros son cuadros reales. Revisado a tamaño real en plano3_ROCCE_tamano_real_c78_84_86_89_94.jpg y plano3_interpolado_tamano_real/. El ambiente de 8008 corre continuo desde 0,167 s: su envolvente es plana (−24 a −27 dBFS cada 50 ms, sin golpes), así que no hay nada que sincronizar con la imagen.',
            '«MIRÁ ESTE DETALLE:»: 76 px alineada a la izquierda (x 60, termina en x ≈ 830) en y 1350, no 1380. El dato va en caja negra en y 1432, no 1480. La caja negra mide 105 px y tiene que terminar antes de y 1540. A 84 px la placa tocaba «Privée» en c103–c107.',
            'Criterio común de la tanda (25/11): los datos sobre fondo claro van en caja negra 50 SemiBold con el mismo cuadro de entrada: «Gianluca, fundador de Roccé» (y 540), «Founders Privée, en celeste» (y 1432), «cielo azul y todo» (y 540) y «ROCCÉ + Founders Privée» (y 540).',
            '«PLANO DE CATÁLOGO.» a 80 px: a 88 pasaba de 940 px.',
            'Placas en dos renglones (máx. 2, ≤ 6 palabras por renglón): «…Y LA TIRAMOS / A LA ARENA.», «FILMADO CON / CELULARES.» y «Aquel video sí era / un anuncio.» (80 px). Halo 0,75 sobre fondo claro.',
            '«Tenías razón.» va en y 650, no en 540: la placa de dos renglones de y 430 baja hasta ≈ 600.',
            'CTA en tres renglones: «Preguntame lo que / quieras de Roccé: / te respondo con video.» (caja blanca de 76 px con pop). En uno o dos renglones pasa de 940 px.',
            'Caja tipeada en dos renglones: «Y ahora, lo que» / «estabas esperando:». Son 34 caracteres, uno por cuadro, en c288–c321; el cursor titila hasta c323.',
            'Flecha del hook al medidor: va por el margen derecho, de (1004, 662) a (950, 426), en la mitad de arriba, donde no rige el límite de x 940.',
            'Color · Blanca: regla común aplicada por plano en la tela lisa (L > 170, sat < 0,15). Si pasa de B−R +12, se lleva a ≤ +8 (objetivo +6), solo en los neutros claros de la tela. Detalle en la tabla.',
            'Solo hook A (condición 3 de Roma: el B va únicamente en MC-01 y MC-03).',
            '_SINMUSICA: ambiente, foley, tecleo, alarma y golpes del medidor, que son interfaz. Para llegar a −14 LUFS sin limitar fuerte lleva un compresor antes del limitador (umbral 0,03, ratio 3) y fx a −3 dB.',
        ],
        personas=['7824 (plano 1): manos y antebrazos tatuados que sostienen la Negra en el balcón. Pendiente quién es (condición 7).',
                  '7887 (plano 2): según el guion, Gianluca de espaldas («EL MODELO: YO.»). Que lo confirme él.',
                  '7999 (plano 4): quien tira la remera, con campera de cuero y pelo largo. Se ve el brazo y la campera, no la cara. Pendiente quién es y su permiso.',
                  '7884 (plano 6): el chico que saca la foto, de perfil con el celular. ¿Gianluca? (condición 7).',
                  '7885 (plano 10): el chico sentado de espaldas con la Negra. ¿Gianluca? (condición 7).',
                  '4530 y 4531 (planos 7 y 11): solo manos, con uñas largas pintadas en 4531. No identificable; se informa igual.'],
        frases=['Concesión «Aquel video sí era un anuncio. Tenías razón.» (alternativa de Fede: «Esta vez, no.»). Necesita el OK de Gianluca.',
                'Compromiso del CTA «Preguntame lo que quieras de Roccé: te respondo con video.»: que Gianluca lo asuma.',
                'Permiso para mostrar el comentario real «me comí alto anuncio» sin usuario.',
                'Serie «Respondo» (promesa del guion; no aparece en pantalla).'],
    ),
}


def main(k):
    cfg = PIEZAS[k]; T = cfg['T']
    ctl = json.load(open(T / 'evidencia_v01' / 'control.json'))
    pj = json.load(open(T / 'planos.json'))
    au = json.load(open(T / 'audio' / 'audio.json'))
    ent = json.load(open(T / 'entrega.json')) if (T / 'entrega.json').exists() else {}
    L = [f'# {cfg["titulo"]} · Hoja de máster v01 · Pedro A · 25/11/2026', '', REGLA, '',
         f'Receta: `{cfg["receta"]}`. Intermedios: `{T}`. Guion: `04_fede_guiones_G1.md`; condiciones: `06_roma_aprobacion_G1.md`; especificación: `05_especificacion_comun.md`.', '']

    # 1. entregables
    L += ['## 1. Entregables e ID inmutable', '']
    filas = []
    for kk, f in ctl['archivos'].items():
        nombre = Path(f['archivo']).name
        filas.append([kk, f'`{nombre}`', f['bytes'], f'`{f["md5_video"]}`', f'`{f["md5_audio"]}`', f'`{f["sha256"][:16]}…`',
                      f"{f['video']['duracion']:.3f} s / {f['audio']['duracion']:.3f} s".replace('.', ','),
                      f"{f['sonoridad']['lufs_integrado']:.1f} LUFS · {f['sonoridad']['pico_dbtp']:.1f} dBTP · LRA {f['sonoridad']['lra']:.1f}".replace('.', ',')])
    L += [tabla(filas, ['Versión', 'Archivo', 'Bytes', 'md5 flujo video', 'md5 flujo audio', 'sha256 (archivo local)', 'Duración v / a', 'Sonoridad']), '']
    L += ['- **ID inmutable** = md5 de los flujos (`ffmpeg -i X -map 0:v -c copy -f md5 -`, ídem audio). La copia de esta carpeta puede llevar una caja C2PA agregada por el almacenamiento: se compara por flujos, no por bytes.',
          '- Máster local: `/home/user/1/EXPORTACIONES/` (fuera de git: el repo es público). Copia: esta carpeta.']
    if ent:
        L += ['- Verificación de la entrega (`entrega.json`):']
        for dst, v in ent.items():
            if dst == 'evidencia':
                L += [f"  - evidencia: {v['archivos_red']} archivos en la carpeta (local {v['archivos_local']})."]
            else:
                L += [f"  - `{dst}`: flujos iguales al máster = **{v['flujos_iguales']}**; archivo idéntico byte a byte = {v['archivo_identico']}."]
    L += ['']

    # 2. ficha
    a = ctl['archivos']['A']
    v, au_ = a['video'], a['audio']
    L += ['## 2. Ficha técnica (ffprobe + decodificación)', '',
          f"- Video: {v['codec']} {v['perfil']} nivel {v['nivel'] // 10},{v['nivel'] % 10}, {v['pix_fmt']}, {v['ancho']}×{v['alto']}, {v['fps']} fps, {v['cuadros']} cuadros, {str(round(v['duracion'], 3)).replace('.', ',')} s; color {'/'.join(v['color'])} (rango/matriz/primarios/transferencia).",
          f"- Audio: {au_['codec'].upper()}-{au_['perfil']}, {au_['hz']} Hz, {au_['canales']} canales, {str(round(au_['duracion'], 3)).replace('.', ',')} s. Audio = video (diferencia < medio cuadro) en todas las versiones: **{all(x['audio_igual_video'] for x in ctl['archivos'].values())}**.",
          f"- `ffmpeg -v error -i X -f null -`: sin errores en todas las versiones = **{all(x['decodifica_completo'] and not x['errores'] for x in ctl['archivos'].values())}**.",
          f"- +faststart (moov antes de mdat): {all(x['faststart_moov_antes_de_mdat'] for x in ctl['archivos'].values())}. Metadatos de ubicación/GPS: {'ninguno' if not any(x['marcas_gps_o_ubicacion'] for x in ctl['archivos'].values()) else 'HAY'} (etiquetas de formato: solo major_brand, minor_version, compatible_brands, encoder).",
          f"- _SINMUSICA con el mismo flujo de video que A (copiado sin recodificar): **{ctl['sinmusica_mismo_video_que_A']}**.", '']

    # 3. línea de tiempo
    L += ['## 3. Línea de tiempo real (máster ↔ fuente) contra el guion', '']
    filas = []
    for p in pj['planos']:
        c0, c1 = p['m0'], p['m0'] + p['cuadros'] - 1
        filas.append([p['id'], f'c{c0}–c{c1} ({s(c0)}–{s(c1 + 1)} s)', p['toma'].replace('IMG_', ''), tramo_fuente(p),
                      cfg['guion'][p['id']], cfg['desvio_plano'].get(p['id'], 'igual al guion')])
    L += [tabla(filas, ['#', 'Máster', 'Toma', 'Cuadros fuente (s fuente)', 'Guion', 'Desvío']), '',
          f"Total: {pj['cuadros']} cuadros = {pj['cuadros'] / 30:.3f}".replace('.', ',') + f" s (guion: {cfg['nf']} c).", '']

    # 4. interfaz
    L += ['## 4. Interfaz, textos y dispositivo de apuesta', '']
    if k == 'mc01':
        mk = ctl['marcador']
        filas = [[f'c{c}', f"{d['puntos'][0]}–{d['puntos'][1]}"] for c, d in sorted(mk['por_cuadro'].items(), key=lambda x: int(x[0]))]
        L += ['Marcador por cuadro (registro de la capa; evidencia `marcador/`). Secuencia del guion: 0–0 → 0–1 c42 → 1–1 c66 → 1–2 c90 → 2–2 c120 → 3–2 c147 → 3–3 c177 → 3–4 c204 → 4–3 c323.', '',
              tabla(filas, ['Cuadro', 'A FAVOR – EN CONTRA']), '']
    else:
        md = ctl['medidor']
        filas = [[f'c{c}', f"{d['numero']} %", f"{d['relleno']:.2f}".replace('.', ','), 'sí' if d['relleno_blanco'] else '']
                 for c, d in sorted(md['por_cuadro'].items(), key=lambda x: int(x[0]))]
        L += ['Medidor «ANUNCIO» por cuadro (registro de la capa; evidencia `medidor/` y `cuadros_A/giro_c323-c329.jpg`). Serie del guion: c30 10 · c60 0 · c78 40 · c114 20 · c150 60 · c186 35 · c222 75 · c258 95 (titila) · c300 99 · c324–c329 → 0.', '',
              tabla(filas, ['Cuadro', 'Número', 'Relleno (%)', 'Titila en blanco']), '',
              f"Burbuja «me comí alto anuncio» + «Comentario en TikTok», sin usuario, en todos los cuadros: **{ctl['burbuja_en_todos_los_cuadros']}**.", '']
    L += ['- Grafías revisadas en la receta y en los cuadros: ROCCÉ / Roccé, «Founders Privée», voseo y puntuación como en el guion. No hay subtítulos, precio, link, rocce.shop ni fechas.',
          '- Cada gráfica responde 6 cuadros después de su corte y lleva su golpe de sonido (eventos en `audio_eventos_completa.json`). Pop 118 → 109 → 100 % en hook, giro y CTA; las placas de evidencia entran secas en el corte.', '']
    zs = ctl['zona_segura_pixeles_visibles']
    zona_ok = (not zs) if isinstance(zs, list) else all(not x for x in zs.values())
    L += [f"- Zona segura medida sobre los píxeles visibles de la capa (y 220–1540; x ≤ 940 en la mitad de abajo), cada texto o gráfica por separado: **{'sin salidas' if zona_ok else 'HAY SALIDAS: ' + json.dumps(zs)[:300]}**.", '']

    # 5. texto vs estampado
    te = ctl['texto_vs_estampado']
    cont = te.get('contactos') or te.get('contactos_A') or {}
    grupos = {}
    for n, x in sorted(cont.items(), key=lambda z: int(z[0])):
        grupos.setdefault(x['revision'], []).append(int(n))

    def rangos(ns):
        out, a0 = [], ns[0]; prev = ns[0]
        for n in ns[1:] + [None]:
            if n is None or n != prev + 1:
                out.append(f'c{a0}' if a0 == prev else f'c{a0}–c{prev}'); a0 = n
            prev = n if n is not None else prev
        return ', '.join(out)
    L += ['## 5. Texto contra estampado (condición 4)', '',
          f"Método: {te['metodo']}. Cuadros revisados: {te.get('cuadros_revisados') or te.get('cuadros_revisados_A')}"
          + (f" (A) y {te['cuadros_revisados_B']} (B, c0–c59)" if 'cuadros_revisados_B' in te else '') + '. El estampado se detecta solo dentro de la zona de prendas de cada plano; cada contacto se miró a tamaño real.', '',
          f"- **Contactos reales: {len(te['contactos_reales'])}** {te['contactos_reales'] if te['contactos_reales'] else ''}"]
    for rev, ns in grupos.items():
        L += [f'- {rangos(ns)}: {rev}.']
    if 'contactos_B' in te:
        L += [f"- Hook B: contactos {len(te['contactos_B'])}."]
    L += ['- Distancia mínima interfaz–estampado en cuadros sin contacto (px, cuadro): ' + ', '.join(f'{d} (c{n})' for d, n in te['distancia_minima_sin_contacto_px']) + '.',
          '- Vistas: `estampado/cNNN.jpg` (rojo = estampado detectado +12 px, amarillo = zona de prendas, con la capa encima).', '']

    # 6. color
    L += ['## 6. Color', '', '### Blanca por plano (criterio común: tela lisa L > 170, sat < 0,15; neutralizar a ≤ +8 si pasa de +12)', '']
    filas = []
    for r in ctl['blanca_tabla']:
        med = r['medidas']
        dsp = [m['despues'] for m in med if m['despues']]
        cel_a = [m['celeste_antes']['tono_grados'] for m in med if m.get('celeste_antes')]
        cel_d = [m['celeste_despues']['tono_grados'] for m in med if m.get('celeste_despues')]
        filas.append([r['plano'], r['toma'].replace('IMG_', ''), f"c{r['cuadros'][0]}–c{r['cuadros'][1]}",
                      ' / '.join(num(x, 0) for x in r['b_menos_r_antes']) if r['b_menos_r_antes'] else '—',
                      ' / '.join(num(x, 0) for x in r['b_menos_r_master']) or '—',
                      ' / '.join(num(m['g_menos_r'], 0) for m in dsp) or '—',
                      'sí' if r['neutralizada'] and ctl['blanca_neutralizada'].get(r['plano'], {}).get('aplicada') else 'no',
                      (' / '.join(f'{x:.0f}°' for x in cel_a) + ' → ' if cel_a else '') + (' / '.join(f'{x:.0f}°' for x in cel_d) if cel_d else '—'),
                      'no' if not any(m['amarillenta'] for m in dsp) else 'SÍ', r['nota']])
    L += [tabla(filas, ['Plano', 'Toma', 'Cuadros', 'B−R sin corregir (3 cuadros)', 'B−R máster', 'G−R máster', 'Neutralizada', 'Tono «Founders Privée» (antes → máster)', 'Amarillenta', 'Nota']), '',
          '- 3 cuadros por plano: 2 después de la entrada, el del medio y 3 antes de la salida. B−R es la mediana de la tela lisa. «Sin corregir» es el intermedio antes de neutralizar; solo existe donde la regla se aplicó.',
          '- Máscaras medidas (verde = tela lisa, magenta = celeste): `blanca_medicion_por_plano.jpg`. «Founders Privée» se mide en los píxeles junto a la tela con B−R > 25 y sat > 0,22; el celeste del arte ronda 205–220°.',
          '- La neutralización usa ganancias por franja de luminancia y por cuadro, suavizadas en el tiempo (gaussiana de 3 cuadros), para que no parpadee. El peso es 0 en el celeste, ROCCÉ, la arena, el cielo y la piel. Una franja con B−R ≤ +8 no se toca.', '']
    neg = {kk: vv for kk, vv in ctl['color'].items() if kk.startswith('negra')}
    L += ['### Negra (nunca marrón: R−B ≤ +6 en la mitad oscura de la tela)', '',
          tabla([[kk, ' / '.join(str(x).replace('.', ',') for x in vv['rgb']), num(vv['r_menos_b'])] for kk, vv in neg.items()], ['Medición', 'RGB medio', 'R−B']), '']
    if ctl.get('negra_neutralizada'):
        for kk, vv in ctl['negra_neutralizada'].items():
            c0 = vv['control'][0]
            L += [f"- Plano {kk}: tela oscura R−B {num(c0['antes']['r_menos_b'])} → {num(c0['despues']['r_menos_b'])} (cuadro {c0['cuadro']} del plano); objetivo {vv['objetivo']}. Antes/después a tamaño real: `negra_plano{kk}_antes_despues.jpg`."]
        L += ['']

    # 7. cámara lenta / rampa
    L += ['## 7. Cámara lenta y rampa (condición 2)', '']
    if k == 'mc01':
        vl = ctl['var_lento']
        L += [f"- VAR (plano 10, c255–c299): mezcla lineal entre cuadros reales vecinos; diferencia media entre cuadros consecutivos {str(vl['dif_media_consecutivos_min']).replace('.', ',')}–{str(vl['max']).replace('.', ',')} (0 = repetido); cuadros idénticos: {vl['cuadros_identicos'] or 'ninguno'}. Sin tartamudeo por construcción (ningún cuadro se repite). A tamaño real no hay letras dobles en ROCCÉ ni en «Founders Privée» (las dos remeras están quietas en la roca): `var_tamano_real/`.", '']
    else:
        rp = ctl['plano3_rampa']
        org = rp.get('origen') or []
        L += [f"- Plano 3 (c72–c107): posiciones de fuente {rp['posiciones_fuente'][0]}…{rp['posiciones_fuente'][-1]}; origen por cuadro: {org.count('real')} reales, {org.count('mci')} interpolados con compensación de movimiento, {org.count('mezcla')} mezclados.",
              '- Diferencia media entre cuadros consecutivos del máster (c73–c107): ' + ', '.join(str(x).replace('.', ',') for x in rp['dif_media_consecutivos_master']) + '. El tramo lento da la mitad que el tramo a 1,0, sin saltos.',
              '- Desplazamiento de la cámara entre cuadros de fuente (correlación de fase a 1/4): ' + ', '.join(f"{d['de']}→{d['a']} {d['px']:.0f}" for d in rp['desplazamiento_px_fuente']) + ' px. Es la razón para no usar mezcla lineal.', '']

    # 8. sonido
    L += ['## 8. Sonido', '', '**No se escuchó.** No hay reproducción de audio en este entorno. Todo lo que sigue sale de mediciones: ebur128, niveles por tramo y registro de eventos.', '']
    filas = []
    for kk, f in ctl['archivos'].items():
        filas.append([kk, f"{f['sonoridad']['lufs_integrado']:.1f}", f"{f['sonoridad']['pico_dbtp']:.1f}", f"{f['sonoridad']['lra']:.1f}",
                      f"{f['niveles']['rms_ultimo_05s_dbfs']:.1f}", ', '.join(f'{t:.1f}' for t in f['niveles']['ventanas_100ms_bajo_menos50dbfs']) or 'ninguna'])
    L += [tabla([[str(x).replace('.', ',') for x in r] for r in filas], ['Versión', 'LUFS integrados', 'Pico dBTP', 'LRA', 'RMS último 0,5 s (dBFS)', 'Ventanas 100 ms < −50 dBFS (s)']), '']
    tr = {kk: f['niveles']['tramos'] for kk, f in ctl['archivos'].items()}
    ks = list(tr)
    filas = []
    for i, t in enumerate(tr[ks[0]]):
        filas.append([t['tramo'], f"{t['t0']:.1f}–{t['t1']:.1f}"] + [f"{tr[kk][i]['rms_dbfs']:.1f} / {tr[kk][i]['pico_dbfs']:.1f}" for kk in ks])
    L += ['Niveles por tramo (RMS / pico de muestra, dBFS):', '', tabla([[str(x).replace('.', ',') for x in r] for r in filas], ['Tramo', 's'] + ks), '']
    for kk in ('completa', 'sinmusica'):
        lim = au[kk].get('limitador', {})
        L += [f"- Mezcla {kk}: limitador `alimiter level=false` con techo del WAV en −2,0 dBTP (AAC suma 0,5–0,7 dB). Reducción máxima {str(lim.get('reduccion_max_db')).replace('.', ',')} dB, en {', '.join(str(x).replace('.', ',') for x in lim.get('en_s', [])[:3])} s; ventanas con más de 1 dB: {str(lim.get('pct_ventanas_mas_de_1db')).replace('.', ',')} %." + (' Con compresión previa: la cifra suma compresor y limitador.' if lim.get('nota') else '')]
    L += ['- Ambiente real de cada toma con las ganancias del guion. ' + cfg['sonido_fuera'] + ' No hay voz. Música TEMP sintetizada con sonido.py, como pide el guion.',
          '- Ventanas bajo −50 dBFS: ' + cfg['silencios'],
          '- Registro completo de eventos (cuadro, segundo, qué suena): `audio_eventos_completa.json` y `audio_eventos_sinmusica.json`. Sonoridad momentánea cada 100 ms: `sonoridad_momentanea_*.json`.', '']

    # 9. evidencia
    L += ['## 9. Evidencia (`evidencia_v01/`)', '',
          '- `cuadros_A/`: c0, antes y después de cada corte (`corte_cNNN.jpg`), giro, CTA y último cuadro, a tamaño real.' + (' `cuadros_B/`: hook B.' if k == 'mc01' else ''),
          '- `hoja_*_cada_0.5s.jpg`: hoja cada 15 cuadros. `vista_360_*.jpg`: lectura a 360 px de ancho, como en un teléfono.',
          '- `estampado/`, `blanca_medicion_por_plano.jpg`' + (', `negra_plano05_antes_despues.jpg`, `var_tamano_real/`, `marcador/`' if k == 'mc01' else ', `plano3_*`, `medidor/`') + ', `hoja_fuente_*.jpg` (hojas de fuente usadas para decidir tramos).',
          '- `control.json`: todas las mediciones de esta hoja. `planos.json`: tramos de fuente, ventanas y color por plano. `audio.json`: mezcla y limitador.', '']

    # 10. desvíos
    L += ['## 10. Desvíos respecto del guion (y por qué)', '']
    L += [f'{i}. {d}' for i, d in enumerate(cfg['desvios'], 1)] + ['']

    # 11. pendientes
    L += ['## 11. Pendiente de confirmar (no frena el v01; frena la publicación)', '', '**Personas:**', ''] + [f'- {x}' for x in cfg['personas']]
    L += ['', '**Frases y permisos (para Gianluca):**', ''] + [f'- {x}' for x in cfg['frases']] + ['']

    # 12. no verificado
    L += ['## 12. Lo que no se verificó', '',
          '- **El audio no se escuchó.** No hay reproducción de audio en el entorno; el sonido se controló con ebur128, niveles y el registro de eventos. Falta escuchar la mezcla, la sincronía real de los golpes y si la música TEMP se siente como pide el guion.',
          '- **No se reprodujo en un teléfono.** La legibilidad se juzgó en vistas a 360 px y la imagen por cuadros sueltos: hojas, cortes y tamaño real. No hubo reproducción continua, así que el ritmo y el movimiento solo se infieren de las diferencias entre cuadros.',
          '- El color se midió en números (B−R, R−B, tono). No se miró en una pantalla calibrada.',
          '- La interpolación con compensación de movimiento (MC-02 plano 3) y la mezcla del VAR (MC-01) se revisaron en cuadros sueltos a tamaño real y en hojas, no en reproducción.' if k == 'mc02' else '- La mezcla del VAR se revisó en cuadros sueltos a tamaño real y en hojas, no en reproducción.',
          '- Personas y frases del punto 11: sin confirmar.', '']
    out = cfg['pieza'] / '01_pedro_hoja_master_v01.md'
    if out.exists():
        raise SystemExit(f'{out} ya existe: no se sobrescribe')
    out.write_text('\n'.join(L), encoding='utf-8')
    print(out, len(L), 'renglones')


if __name__ == '__main__':
    main(sys.argv[1])
