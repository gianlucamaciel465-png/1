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

# v05 = la ejecución de los pines del perfil de Gianluca (capturas IMG_5539–5541 del 25/11; medidas en la hoja de Pedro):
# MAYÚSCULAS en Anton centradas en el tercio superior, relleno blanco → gris claro por renglón con el acento celeste,
# sombra oscura marcada, logo «1» recortado (LOGO/ROCCE_logo_sin_fondo.png) centrado justo debajo; sin firma ni ficha.
# Mismas frases que v04. Fotos (cambio de Roma por los guardados medidos por Pepe): P4 con las remeras (7895), P5 y P6 frase
# sola sobre una toma de ambiente propia sin la prenda (no hay tomas de noche ni de atardecer: las más sobrias, nubladas).
_OSC = (12, 18, 26)   # mismo color de degradé que v01–v04
# Degradé oscuro arriba (queda en el pin «sin frase»: cuenta para el contraste, como en v04): 0,74 → 0,64 hasta 5 px debajo
# de la última línea de base y se apaga en 220 px, para que el logo negro quede sobre un fondo medio (sin borde: no es
# oscuro). Sombra: una dura corta (dy 5 % de la mayúscula, alfa 0,65) + un halo blando (desenfoque 10 %, alfa 0,55).
_SOMBRA = dict(dura=(0.05, 0.012, 0.65), halo=(0.03, 0.10, 0.55))
# Roma (25/11): acento = el celeste medido en su pin «GIVE HISTORY YOUR NAME» (#B2E2FD, #C4E8FD arriba);
# el #CDDDE5 de v04 se leía blanco a 180 px.
PINES['v05'] = [
    # P4 · con remera · 7895 a 0,4 s: las dos remeras en la roca con la ola reventando atrás. Caja más cerrada que v04
    # (1700 contra 1800) y corrida a la derecha: remeras x 740–1660 de la toma → 23–77 % del ancho; frase y logo sobre
    # mar y ola (y < 1300 de la toma); las remeras empiezan en y 1640.
    dict(id='p4', nombre='ROCCE_LIFE_PIN_04_agrandado_v05', estilo='anton', fuente=('toma', 'IMG_7895', 0.4),
         caja=(350, 0, 1700), frase_txt='QUERER MÁS NO TE HACE AGRANDADO.',
         lineas=[[('QUERER MÁS', None)], [('NO TE HACE', None)], [('AGRANDADO.', 'c')]],
         fs=162, top=110, logo_h=120, logo_gap=36, con_remera=True, sombra=_SOMBRA, acento=('#C4E8FD', '#B2E2FD'),
         motivo_foto='la misma de v04 (pedido de Roma): las dos remeras enteras con la ola reventando atrás',
         grads=[dict(lado='top', alto=792, color=_OSC, stops=[(0, 0.74), (72.2, 0.64), (100, 0)])]),
    # P5 · frase sola · 7857 a 0,0 s: rocas vacías frente al mar picado, cielo nublado (el cuadro antes de que entre él).
    dict(id='p5', nombre='ROCCE_LIFE_PIN_05_quedate_igual_v05', estilo='anton', fuente=('toma', 'IMG_7857', 0.0),
         caja=(0, 0, 2160), frase_txt='NADIE TE APLAUDE POR QUEDARTE. QUEDATE IGUAL.',
         lineas=[[('NADIE TE APLAUDE', None)], [('POR QUEDARTE.', None)], [('QUEDATE IGUAL.', 'c')]],
         fs=127, top=120, logo_h=120, logo_gap=36, con_remera=False, sombra=_SOMBRA, acento=('#C4E8FD', '#B2E2FD'),
         motivo_foto='lugar vacío con horizonte: rocas frente al mar picado, nadie mirando',
         grads=[dict(lado='top', alto=703, color=_OSC, stops=[(0, 0.74), (68.7, 0.64), (100, 0)])]),
    # P6 · frase sola · 7793 a 0,0 s: la playa de la ciudad nublada desde el balcón, antes del paneo a la remera.
    # Caja hasta y 2520: deja afuera los autos y a los dos peatones cercanos de las esquinas (y > 2550).
    dict(id='p6', nombre='ROCCE_LIFE_PIN_06_enero_excusas_v05', estilo='anton', fuente=('toma', 'IMG_7793', 0.0),
         caja=(60, 0, 1680), frase_txt='ENERO TAMBIÉN VA A TENER EXCUSAS.',
         lineas=[[('ENERO ', None), ('TAMBIÉN', 'c')], [('VA A TENER', None)], [('EXCUSAS.', None)]],
         fs=144, top=140, logo_h=120, logo_gap=36, con_remera=False, sombra=_SOMBRA, acento=('#C4E8FD', '#B2E2FD'),
         motivo_foto='la playa de la ciudad fuera de temporada, nublada: el lugar de enero, todavía gris',
         grads=[dict(lado='top', alto=771, color=_OSC, stops=[(0, 0.74), (71.5, 0.64), (100, 0)])]),
]

# v06 (25/11, después del rechazo de v05: «Muy malos, nada que ver a los míos. Podes usar fotos de otras personas y hace
# frases mas motivadoras y con más sentido. SIEMPRE EL LOGO DE ROCCÉ TAL CUAL ES, sin deformarlo»).
# Fotos de otras personas, de Burst (Shopify): licencia Burst, uso comercial libre, se puede modificar, sin atribución
# obligatoria (no se puede vender la foto sola). Bajadas a TRABAJO/life2/pines_v06/fotos/ (fuera de git).
# Lo que cambia contra v05, medido en sus pines: foto con una persona y luz real (noche, contraluz), sin velo oscuro
# pesado; frase más grande (renglón más ancho ≈ 82–86 % del pin); una inclinada como «SI VAS A FALLAR»; sombra con
# relieve (una dura más larga + halo). Logo: el mismo PNG, solo escalado; sobre fondo oscuro, borde blanco fino como
# en sus pines oscuros («SI VAS A FALLAR», «NO ESTÁS ATRASADO»).
_SOMBRA6 = dict(dura=(0.06, 0.006, 0.85), halo=(0.02, 0.12, 0.60))
_CEL = ('#C4E8FD', '#B2E2FD')
_F6 = 'TRABAJO/life2/pines_v06/fotos/'
PINES['v06'] = [
    # P7 · persona sola sentada arriba de una calle en pendiente, la ciudad de noche abajo (San Francisco).
    # Retoque: se sacaron los cuernos rojos del gorro (disfraz) con scripts/life/retoque_cuernos.py.
    dict(id='p7', nombre='ROCCE_LIFE_PIN_07_nadie_lo_ve_v06', estilo='anton',
         fuente=('externa', _F6 + 'hill_sin_cuernos.jpg'), caja=(1, 0, 3844),
         frase_txt='HOY NADIE LO VE. MAÑANA NADIE VA A PODER IGNORARLO.',
         lineas=[[('HOY NADIE LO VE.', None)], [('MAÑANA NADIE', None)], [('VA A PODER', None)], [('IGNORARLO.', 'c')]],
         fs=124, top=100, inter=1.20, extra={1: 18}, logo_h=120, logo_gap=36, con_remera=False, sombra=_SOMBRA6, acento=_CEL,
         logo_borde=True, logo_borde_px=2,
         foto='Burst · hooded-figure-sits-on-city-street-hill (licencia Burst)',
         motivo_foto='una persona sola mirando la ciudad de noche desde arriba: lo que todavía nadie ve',
         grads=[dict(lado='top', alto=900, color=_OSC, stops=[(0, 0.50), (75, 0.38), (100, 0)])]),
    # P8 · alguien caminando solo de noche por una vereda mojada, hacia la luz (Berlín). Inclinada.
    dict(id='p8', nombre='ROCCE_LIFE_PIN_08_cansado_v06', estilo='anton',
         fuente=('externa', _F6 + 'night-walk-on-city-street.jpg'), caja=(1162, 0, 1650),
         frase_txt='CANSADO SE PUEDE SEGUIR. RENDIDO, NO.',
         lineas=[[('CANSADO', None)], [('SE PUEDE SEGUIR.', None)], [('RENDIDO, NO.', 'c')]],
         fs=124, top=100, logo_h=120, logo_gap=36, con_remera=False, sombra=_SOMBRA6, acento=_CEL, oblicua=9,
         logo_borde=True, logo_borde_px=2,
         foto='Burst · night-walk-on-city-street (licencia Burst)',
         motivo_foto='seguir caminando de noche, solo, con la vereda mojada',
         grads=[dict(lado='top', alto=760, color=_OSC, stops=[(0, 0.45), (72, 0.40), (100, 0)])]),
    # P9 · una persona sola en la orilla, el mar entrando, cielo de atardecer.
    dict(id='p9', nombre='ROCCE_LIFE_PIN_09_caerse_v06', estilo='anton',
         fuente=('externa', _F6 + 'a-figure-in-a-hoodie-on-a-beach-at-the-shoreline.jpg'), caja=(375, 0, 1492),
         frase_txt='CAERSE ES PARTE. QUEDARSE EN EL PISO ES UNA DECISIÓN.',
         lineas=[[('CAERSE ES PARTE.', None)], [('QUEDARSE EN EL PISO', None)], [('ES UNA DECISIÓN.', 'c')]],
         fs=110, top=116, inter=1.20, extra={2: 8}, logo_h=120, logo_gap=36, con_remera=False, sombra=_SOMBRA6, acento=_CEL,
         foto='Burst · a-figure-in-a-hoodie-on-a-beach-at-the-shoreline (licencia Burst)',
         motivo_foto='de pie, sola frente al mar: la decisión de no quedarse en el piso',
         grads=[dict(lado='top', alto=760, color=_OSC, stops=[(0, 0.58), (62, 0.46), (100, 0)])]),
]
