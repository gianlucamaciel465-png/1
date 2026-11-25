# Roccé Life · configuración de pines por versión (frases, fondo real, recorte 2:3 y composición).
PINES = {
    # v00 = prueba de tipografía y legibilidad con frases provisorias (no se entrega)
    'v00': [
        dict(id='t1', nombre='prueba_8002', fuente=('toma', 'IMG_8002', 0.1), caja=(0, 0, 2160),
             frase_html='Que tu historia<br>lleve tu <em>nombre</em>.', frase_txt='Que tu historia lleve tu nombre.',
             pos_frase='top:150px', pos_firma='left:76px;bottom:70px', fs=112),
        dict(id='t2', nombre='prueba_7887', fuente=('toma', 'IMG_7887', 2.2), caja=(0, 300, 2160),
             frase_html='Empezá con<br>lo que <em>tenés</em>.', frase_txt='Empezá con lo que tenés.',
             pos_frase='top:130px', pos_firma='left:76px;bottom:70px', fs=118, grad=('top', 760, 0.55, (12, 18, 26))),
        dict(id='t3', nombre='prueba_roca_ola', fuente=('foto', 'blanca_espalda_roca_ola.jpg'), caja=(84, 0, 1344),
             frase_html='Casi es la prueba<br>de que estás <em>cerca</em>.', frase_txt='Casi es la prueba de que estás cerca.',
             pos_frase='top:130px', pos_firma='left:76px;bottom:70px', fs=100, grad=('top', 760, 0.5, (12, 18, 26))),
    ],
}

# v01 = las tres frases aprobadas por Roma (05_roma_filtro_ideas.md), sistema Instrument Serif + cursiva en una palabra,
# firma «ROCCÉ LIFE» + logo original en ficha #FEFEFE abajo a la izquierda (lejos de los botones de Pinterest).
FIRMA = 'left:72px;bottom:66px'
PINES['v01'] = [
    # P1 · Disciplina · Gianluca (confirmado en 7887) de espaldas con la Negra, le saca la foto a la Blanca; ola atrás.
    dict(id='p1', nombre='ROCCE_LIFE_PIN_01_esta_parte_v01', fuente=('toma', 'IMG_7887', 1.067), caja=(260, 500, 1900),
         neutro=(560, 1700, 1400, 2330),
         frase_html='<em>Esta parte</em><br>no sale en la foto.', frase_txt='Esta parte no sale en la foto.',
         pos_frase='top:112px', pos_firma=FIRMA, fs=122, grad=('top', 720, 0.62, (12, 18, 26))),
    # P2 · Presencia · la Negra presentada (7824), ROCCÉ tono sobre tono; texto sobre la tela negra lisa.
    # 5,9 s y no 5,6: a 5,6 la «F» y la última «e» de «Founders Privée» quedan cortadas por el borde; a 5,9 el estampado
    # entra completo (x 67–1880). Entran los dedos que la presentan (sin tatuajes a la vista) y algo de jardín abajo a los lados.
    dict(id='p2', nombre='ROCCE_LIFE_PIN_02_no_grita_v01', fuente=('toma', 'IMG_7824', 5.9), caja=(0, 700, 1960),
         frase_html='No grita.<br><em class="c">Se nota.</em>', frase_txt='No grita. Se nota.',
         pos_frase='top:920px', pos_firma=FIRMA, fs=142, alinear='center'),
    # P3 · Ambición · la Blanca en la roca con la ola rompiendo atrás (foto de PRODUCTO).
    dict(id='p3', nombre='ROCCE_LIFE_PIN_03_donde_rompe_v01', fuente=('foto', 'blanca_espalda_roca_ola.jpg'),
         caja=(84, 0, 1344),
         frase_html='Andá hasta<br>donde <em>rompe</em>.', frase_txt='Andá hasta donde rompe.',
         pos_frase='top:112px', pos_firma=FIRMA, fs=132, grad=('top', 720, 0.5, (12, 18, 26))),
]

# v02 = correcciones del dictamen independiente de Roma (24/11): P1 neutralización solo sobre la Blanca (la Negra queda
# igual, medido) y recorte más cerrado para que el gesto del celular se lea en el feed; P2 frase en acción («No lo grites.
# Que se note.») con la original como alternativa; P3 degradé 0,62 como P1; margen de la frase = margen de la firma (72).
import copy as _c
_v = {p['id']: _c.deepcopy(p) for p in PINES['v01']}
for _p in _v.values():
    _p['nombre'] = _p['nombre'].replace('_v01', '_v02'); _p['mx'] = 72
_v['p1'].update(caja=(460, 650, 1700))
_v['p2'].update(nombre='ROCCE_LIFE_PIN_02_que_se_note_v02', frase_html='No lo grites.<br><em class="c">Que se note.</em>',
                frase_txt='No lo grites. Que se note.')
_p2b = _c.deepcopy(_v['p2']); _p2b.update(id='p2b', nombre='ROCCE_LIFE_PIN_02B_no_grita_v02',
                                         frase_html='No grita.<br><em class="c">Se nota.</em>', frase_txt='No grita. Se nota.')
_v['p3'].update(grad=('top', 780, 0.75, (12, 18, 26)))   # 0,75: 98 % del trazo ≥ 3:1 (0,62 daba 83 %)
PINES['v02'] = [_v['p1'], _v['p2'], _v['p3'], _p2b]


# v03 = tanda 2 (25/11/2026): frases de Cata aprobadas por Roma (TANDA2/04_roma_filtro_ideas_t2.md); la marca del logo
# bien visible (ficha de 128–160 px en vez de 72) porque Gianluca pidió pines «que tengan la marca del logo roccé».
# P6 es solo frase con marca, sobre el azul marino del cierre de marca de R3 (#0f1929 → #0a1522, ESTILO_REFERENCIAS).
PINES['v03'] = [
    # P4 · Ambición · 7885 a 0,2 s: de espaldas con la Negra frente a la Blanca, la ola revienta a la izquierda.
    dict(id='p4', nombre='ROCCE_LIFE_PIN_04_agrandado_v03', fuente=('toma', 'IMG_7885', 0.2), caja=(0, 0, 2160),
         frase_html='Querer más no te hace<br><em>agrandado</em>.', frase_txt='Querer más no te hace agrandado.',
         pos_frase='top:96px', fs=94, mx=72, logo=128, ffs=24, pos_firma='left:72px;bottom:72px',
         grad=('top', 560, 0.62, (12, 18, 26)), grad2=('bottom', 420, 0.55, (12, 18, 26))),
    # P5 · Disciplina · la Blanca sola en la roca entre la espuma (foto de PRODUCTO, nítida).
    dict(id='p5', nombre='ROCCE_LIFE_PIN_05_quedate_igual_v03', fuente=('foto', 'blanca_espalda_rocas_espuma.jpg'),
         caja=(0, 0, 1717),
         frase_html='Nadie te aplaude<br>por quedarte.<br>Quedate <em>igual</em>.',
         frase_txt='Nadie te aplaude por quedarte. Quedate igual.',
         pos_frase='top:84px', fs=96, mx=72, logo=128, ffs=24, pos_firma='left:72px;bottom:72px',
         grad=('top', 620, 0.72, (12, 18, 26)), grad2=('bottom', 420, 0.6, (12, 18, 26))),
    # P6 · Tomar acción · solo frase con marca: azul marino de R3, frase centrada en el tercio superior, logo grande debajo.
    dict(id='p6', nombre='ROCCE_LIFE_PIN_06_enero_excusas_v03', fuente=('color', '#0f1929', '#0a1522'),
         caja=(0, 0, 1000),
         frase_html='Enero<br><em class="c">también</em><br>va a tener<br>excusas.',
         frase_txt='Enero también va a tener excusas.',
         pos_frase='top:250px', fs=150, lh='0.98', mx=72, alinear='center', logo=160, ffs=26,
         pos_firma='left:0;right:0;top:1060px;justify-content:center;flex-direction:column;gap:26px',
         sombra='none', sombra_f='none'),
]

# v04 = correcciones del dictamen independiente de Roma sobre v03 (25/11): P5 la caja (0,0,1717) cortaba la manga derecha
# de la Blanca, que en la foto termina en x 1782 → caja desde x 215 (la izquierda ya viene cortada en la foto) y degradé de
# abajo reducido a 300 px / 0,5 para no agrisar el ruedo; P4 pasa a 7895 a 0,4 s (las dos remeras con la ola reventando
# atrás, sin persona): a 180 px ya no se confunde con v02 P1 y no depende de un consentimiento.
_v4 = {p['id']: _c.deepcopy(p) for p in PINES['v03']}
for _p in _v4.values():
    _p['nombre'] = _p['nombre'].replace('_v03', '_v04')
_v4['p4'].update(fuente=('toma', 'IMG_7895', 0.4), caja=(260, 0, 1800), grad=('top', 640, 0.78, (12, 18, 26)))  # 0,62 daba 86 % del trazo ≥ 3:1
_v4['p5'].update(caja=(215, 0, 1717), grad2=('bottom', 300, 0.5, (12, 18, 26)))
PINES['v04'] = [_v4['p4'], _v4['p5'], _v4['p6']]
