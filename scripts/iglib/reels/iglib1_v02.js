// IGLIB-1 «La tercera tarjeta» · v02 (con locución Firme 04, 10_roma_locucion_G1.1.md) · 885 cuadros a 30 fps (29,50 s).
// Misma pieza que v01 (iglib1.js): mismos textos, orden y tarjeta resaltada; la línea de tiempo se recalcula con la
// duración real de cada frase (voz/locucion.json). Los tramos de la hoja (1–8) reutilizan las animaciones de v01 con un
// mapa de tiempo por anclas (cuadro nuevo → cuadro de v01); el tramo 9 (entra la tercera tarjeta con «Había una
// tercera.» y asienta con «Vos.»), el 10 y el CTA se escriben en cuadros nuevos. Los videos van cuadro a cuadro.
'use strict';
const ESCENA = (() => {
  const N = 885;
  let A = {};                                 // datos: seguimiento del estampado, rutas
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x)), lerp = (a, b, t) => a + (b - a) * t;
  const eio = x => (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2), eo = x => 1 - Math.pow(1 - x, 3), lin = x => x;
  function kf(f, keys, ease = eio) {
    if (f <= keys[0][0]) return keys[0][1];
    for (let i = 0; i < keys.length - 1; i++) { const [a, va] = keys[i], [b, vb] = keys[i + 1];
      if (f <= b) { const u = (keys[i + 1][2] || ease)(clamp((f - a) / (b - a))); return Array.isArray(va) ? va.map((v, j) => lerp(v, vb[j], u)) : lerp(va, vb, u); } }
    return keys[keys.length - 1][1];
  }
  const ent = (f, a, b) => clamp((f - a) / (b - a));
  // ---------- tramos (cuadros de salida, inclusivos)
  // tramos de v01 (cuadros viejos) para las animaciones de la hoja reutilizadas
  const T = { t1: [0, 44], t2: [45, 86], t3: [87, 131], t4: [132, 167], t5: [168, 203], t6: [204, 248], t7: [249, 308],
    t8: [309, 344], t9: [345, 434] };
  // tramos de v02 (cuadros nuevos). Cada frase entra 1 cuadro después del corte (v01 en c0) y deja 2–3 cuadros de aire.
  const T2 = { t1: [0, 100], t2: [101, 153], t3: [154, 200], t4: [201, 247], t5: [248, 320], t6: [321, 394], t7: [395, 527],
    t8: [528, 563], t9: [564, 636], t10: [637, 677], t11: [678, 710], t12: [711, 737], t13: [738, 773], t14: [774, 884] };
  const en2 = (g, t) => g >= T2[t][0] && g <= T2[t][1];
  // mapa nuevo → viejo para los tramos 1–8 (anclas [nuevo, viejo]; lineal entre anclas). Los movimientos (toque, barridos
  // del carrusel, bajada del dedo) conservan su duración; lo que se estira son las esperas, mientras habla la voz.
  // 491 ↔ 273: «Ganó Estudiantes, 2-0.» entra cuando la voz dice «ganó Estudiantes» (v07 + 3,18 s).
  const MAPA = [[0, 0], [100, 44], [101, 45], [103, 47], [109, 53], [139, 68], [145, 74], [147, 80], [153, 86],
    [154, 87], [175, 108], [200, 131], [201, 132], [219, 150], [247, 167], [248, 168], [268, 188], [320, 203],
    [321, 204], [347, 230], [394, 248], [395, 249], [414, 268], [490, 272], [491, 273], [527, 308], [528, 309], [563, 344]];
  function viejo(g) {
    for (let i = 0; i < MAPA.length - 1; i++) { const [a, va] = MAPA[i], [b, vb] = MAPA[i + 1];
      if (g >= a && g <= b) return b === a ? va : va + (vb - va) * (g - a) / (b - a); }
    return MAPA[MAPA.length - 1][1];
  }
  // ---------- textos exactos
  const ENC = 'FINAL · SÁB 28/11 · 17:00 · CENTENARIO';
  const GRANDES = [
    { t: [0, 44], px: 86, lineas: ['Dos tarjetas.', '¿Cuál tocás?'] },
    { t: [45, 86], px: 62, lineas: ['Estudiantes busca su quinta.'] },
    { t: [87, 131], px: 62, lineas: ['Palmeiras ya ganó 3:', '1999, 2020 y 2021.'] },
    { t: [132, 167], px: 62, lineas: ['Palmeiras perdió', 'la final 2025.'] },
    { t: [168, 203], px: 62, lineas: ['Estudiantes no gana', 'una desde 2009.'] },
    { t: [204, 248], px: 62, lineas: ['Palmeiras ya ganó una final', 'en el Centenario: 2021.'] },
    { t: [249, 272], px: 60, lineas: ['Mismos dos. Mismo estadio. 1968.'] },
    { t: [273, 308], px: 60, lineas: ['Mismos dos. Mismo estadio. 1968.', 'Ganó Estudiantes, 2-0.'], nueva: 1 },
    { t: [309, 434], px: 86, lineas: ['¿Cuál tocás?'] },
  ];
  const FINALES = [[450, 488, 'TU FINAL · LUNES 7:00'], [489, 527, 'TU FINAL · LUNES 13:00'], [528, 563, 'TU FINAL · LUNES 22:00']];

  function textoSombra(ctx, s, x, y, px, color = '#ffffff', peso = 700, fam = 'InterDisplay', alfa = 1) {
    ctx.save(); ctx.globalAlpha = alfa; ctx.font = `${peso} ${px}px ${fam}`; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    ctx.shadowColor = 'rgba(0,0,0,0.55)'; ctx.shadowBlur = 14; ctx.shadowOffsetY = 3; ctx.fillStyle = color; ctx.fillText(s, x, y); ctx.restore();
  }
  function ancho(ctx, s, px, peso = 700, fam = 'InterDisplay') { ctx.font = `${peso} ${px}px ${fam}`; return ctx.measureText(s).width; }
  const avisos = [];
  function encabezado(ctx, f, alfa) {
    if (alfa <= 0) return;
    textoSombra(ctx, ENC, 540, 168, 40, 'rgba(255,255,255,0.86)', 600, 'Inter', alfa);
    const g = GRANDES.find(g => f >= g.t[0] && f <= g.t[1]); if (!g) return;
    const lh = g.px * 1.16; const y0 = g.px > 80 ? 284 : (g.lineas.length === 1 ? 300 : 272);
    g.lineas.forEach((l, k) => {
      const w = ancho(ctx, l, g.px); if (w > 984) avisos.push(`texto ancho ${Math.round(w)}: ${l}`);
      // entrada corta (3 cuadros) en cada cambio, salvo c0 (el gancho se lee completo en el primer cuadro)
      const t0 = g.nueva && k === 0 ? -99 : g.t[0]; const u = t0 <= 0 ? 1 : eo(ent(f, t0 - 1, t0 + 2));   // en el cuadro del corte ya se lee
      textoSombra(ctx, l, 540, y0 + lh * k + 14 * (1 - u), g.px, '#ffffff', 700, 'InterDisplay', alfa * u);
    });
  }
  // ---------- carrusel y gestos por cuadro
  const sliverKeys1 = [[87, 0], [96, 0.93, eo], [97, 0.98], [98, 1.002], [99, 1.035, lin], [100, 1.055, lin], [101, 1.03, lin], [102, 1.003, lin], [104, 0.994], [108, 1]];
  const sliverKeys2 = [[168, 0], [175, 0.93, eo], [176, 0.975], [177, 1.0], [178, 1.03, lin], [179, 1.055, lin], [180, 1.045, lin], [181, 1.02, lin], [182, 1.003, lin], [184, 0.995], [188, 1]];
  function carrusel(f) {
    if (f <= 86) return 0;
    if (f <= 131) return kf(f, sliverKeys1);
    if (f <= 167) return kf(f, [[132, 1], [143, -0.035, eo], [150, 0]]);
    if (f <= 203) return kf(f, sliverKeys2);
    if (f <= 251) return 1;
    if (f <= 308) return kf(f, [[251, 1], [261, -0.03, eo], [268, 0]]);
    if (f <= 344) return kf(f, [[309, 0], [319, 0.5]]);
    return kf(f, [[345, 0.5], [355, 2, eo]]);
  }
  const OCULTA = 323;                       // la tarjeta 3 queda a 2 px fuera del borde derecho con el carrusel en 1
  // ---------- tramo 9 en cuadros nuevos: 564 empieza el barrido con «Había una tercera.»; aterriza en 605 (golpe) y
  // «Vos.» entra en 606; el dedo toca GIVE HISTORY YOUR NAME. en 628.
  const G9 = { ini: 564, asienta: 605, toque: 628, fin: 636 }, ZF = 1.06;
  function estado9(g) {
    const c = kf(g, [[564, 0.5], [602, 2.03, eio], [605, 1.995, lin], [608, 2]]); const u9 = eio(ent(g, 564, 602));
    const sel = [0, 1, 2].map(i => i === 2 ? 1 : clamp(1 - Math.abs(c - i) * 2));
    return { c, sel, brillo: [0, 0, kf(g, [[603, 0], [606, 1], [618, 0.25]])], tercera: true, oculta: OCULTA * (1 - u9), puntos3: u9,
      zoom: { z: kf(g, [[607, 1], [636, ZF, lin]]), px: 540, py: HOJA.Y(HOJA.AV_Y) }, botonCeleste: ent(g, 598, 603),
      hundido: kf(g, [[627, 0], [629, 1, eo], [633, 1], [636, 0.3]]), foto3: foto3(g) };
  }
  function estadoHoja(f) {
    const c = carrusel(f); const u9 = eo(ent(f, 345, 355));
    const sel = [0, 1, 2].map(i => i === 2 ? 1 : clamp(1 - Math.abs(c - i) * 2));   // la tercera siempre con borde celeste
    const brillo = [
      Math.max(kf(f, [[48, 0], [55, 1], [70, 1], [84, 0]]), kf(f, [[145, 0], [150, 1], [158, 1], [166, 0]]), kf(f, [[262, 0], [268, 1], [285, 1], [306, 0]])),
      Math.max(kf(f, [[104, 0], [110, 0.6], [128, 0]]), kf(f, [[184, 0], [190, 0.6], [202, 0]])),
      kf(f, [[353, 0], [356, 1], [366, 0.25]])];
    const zoom = f >= 255 && f <= 320 ? { z: kf(f, [[258, 1], [308, 1.05, lin], [318, 1]]), px: 540, py: 1140 }
      : f >= 355 ? { z: kf(f, [[357, 1], [434, 1.08, lin]]), px: 540, py: HOJA.Y(HOJA.AV_Y) } : { z: 1 };
    return { c, sel, brillo, tercera: f >= 87, oculta: OCULTA * (1 - u9), puntos3: u9, zoom,
      botonCeleste: ent(f, 350, 354), hundido: kf(f, [[425, 0], [427, 1, eo], [431, 1], [434, 0.3]]), foto3: null };
  }
  // ---------- video en el círculo de la tarjeta 3: IMG_7859 0,50–3,50 (cuadros 15–104), recorte que sigue «ROCCÉ»
  function recorte7859(n) { const v = A.track[n]; const side = v.ws * 1.58; return [v.cxs + v.ws * 0.05 - side / 2, v.cys + v.ws * 0.24 - side / 2, side, side]; }
  const n7859 = g => 15 + (g - G9.ini);       // el video del círculo empieza en el cuadro 15 de IMG_7859 al entrar la tarjeta
  function foto3(g) { return (ctx, cx, cy, r) => { const n = n7859(g); const im = A.img['v']; const [sx, sy, sw, sh] = recorte7859(n);
    ctx.drawImage(im, sx, sy, sw, sh, cx - r, cy - r, 2 * r, 2 * r); }; }
  function dedoHoja(ctx, f, g) {
    const Y = HOJA.Y; const yc = 1150, yb = Y(2217);
    let x, y, a = 0, p = 0, onda = -1;
    const jit = k => Math.sin(g * 2.3 + k) * 4 + Math.sin(g * 3.7 + 2 * k) * 2;   // temblor en cuadros nuevos
    if (f <= 79) { x = 560; y = yc + 245; a = 1; p = kf(f, [[47, 0], [53, 1, eo], [68, 1], [74, 0]]); if (f >= 53 && f <= 68) onda = (f - 53) / 15;
      if (f < 47) { const u = clamp((47 - f) / 3); x += jit(3) * 0.8 * u; y += jit(5) * 0.5 * u; } }   // tramo 1: duda sobre la tarjeta 1
    else if (f <= 104) { [x, y] = kf(f, [[80, [560, yc + 245]], [86, [770, yc]], [99, [250, yc], eo]]); a = kf(f, [[99, 1], [104, 0]]); p = f >= 86 && f <= 99 ? 0.5 : 0; }
    else if (f <= 127) { a = 0; }
    else if (f <= 150) { [x, y] = kf(f, [[128, [290, yc]], [132, [290, yc]], [143, [820, yc], eo]]); a = kf(f, [[128, 0], [131, 1], [145, 1], [150, 0]]); p = f >= 132 && f <= 143 ? 0.5 : 0; }
    else if (f <= 163) { a = 0; }
    else if (f <= 184) { [x, y] = kf(f, [[164, [790, yc]], [168, [790, yc]], [177, [260, yc], eo]]); a = kf(f, [[164, 0], [167, 1], [179, 1], [184, 0]]); p = f >= 168 && f <= 177 ? 0.5 : 0; }
    else if (f <= 204) { a = 0; }
    else if (f <= 253) {   // tramo 6: baja hasta quedar a milímetros del botón; tiembla; en 249 se suelta
      [x, y] = kf(f, [[206, [540, yc + 30]], [230, [540, yb - HOJA.D(66) - 47]]]); x += f > 230 ? jit(0) * 0.5 : 0;
      a = kf(f, [[205, 0], [209, 1], [249, 1], [253, 0]]); if (f >= 249) y -= (f - 249) * 18;
    }
    else if (f <= 266) { [x, y] = kf(f, [[252, [300, yc]], [261, [820, yc], eo]]); a = kf(f, [[252, 0], [254, 1], [262, 1], [266, 0]]); p = f <= 261 ? 0.5 : 0; }
    else if (f <= 308) { a = 0; }
    else if (f <= 344) {   // tramo 8: arrastra hasta la mitad; después tiembla sobre el botón sin tocarlo
      if (f <= 321) { [x, y] = kf(f, [[309, [300, yc]], [319, [580, yc]]]); a = kf(f, [[309, 0.6], [311, 1], [319, 1], [322, 0]]); p = 0.5; }
      else { x = 540 + jit(1); y = yb - HOJA.D(66) - 44 + jit(2) * 0.6; a = kf(f, [[322, 0], [326, 1]]); }
    }
    // la vista de la hoja puede estar con zoom: el dedo sigue la misma transformación
    const z = estadoHoja(f).zoom; if (z.z && z.z !== 1 && x !== undefined) { x = z.px + (x - z.px) * z.z; y = z.py + (y - z.py) * z.z; }
    if (x !== undefined) HOJA.dedo(ctx, x, y, a, p, onda);
  }
  function dedo9(ctx, g) {
    const Y = HOJA.Y; const yc = 1150, yb = Y(2217); let x, y, a = 0, p = 0, onda = -1;
    if (g <= 610) { [x, y] = kf(g, [[564, [930, yc]], [602, [120, yc], eio]]); a = kf(g, [[564, 0.5], [566, 1], [602, 1], [607, 0]]); p = g <= 602 ? 0.6 : 0; }
    else { [x, y] = kf(g, [[612, [700, yb + 120]], [626, [540, yb]]]); a = kf(g, [[612, 0], [617, 1], [636, 1]]);
      p = kf(g, [[626, 0], [628, 1, eo], [633, 1], [636, 0.4]]); if (g >= 628) onda = (g - 628) / 9; }
    const z = estado9(g).zoom; x = z.px + (x - z.px) * z.z; y = z.py + (y - z.py) * z.z;
    HOJA.dedo(ctx, x, y, a, p, onda);
  }
  // ---------- ventanas de video con relleno desenfocado de la misma toma
  function ventana(ctx, im, sx, sy, sw, sh, dx, dy, dw, dh, r = 0) {
    ctx.save(); HOJA.rr(ctx, dx, dy, dw, dh, r); ctx.clip(); ctx.drawImage(im, sx, sy, sw, sh, dx, dy, dw, dh); ctx.restore();
  }
  const VEN52 = { w: 1080, h: 998, y: (1920 - 998) / 2 };      // ventana 52 % del alto
  const X10 = 698;                                             // recorte fijo 2337×2160 centrado en la espalda (tramo 10)
  // CTA: 7859 cuadros 139–249; el recorte de 2337×2160 sigue el centro de «ROCCÉ» (7859_cta.json, suavizado) porque la
  // cámara se acerca y se aleja; «Founders Privée» (≈ 1,55 × el ancho de ROCCÉ) entra completo.
  const X14 = n => clamp(A.cta[n].cxs + 0.03 * A.cta[n].ws - 2337 / 2, 0, 3840 - 2337);
  const nCTA = g => 139 + (g - T2.t14[0]);
  function rotulo(ctx, s, f0) {               // «TU FINAL · LUNES …»: caja negra, blanco SemiBold (fondo claro: 06 §4)
    const px = 64; ctx.font = `700 ${px}px InterDisplay`; const w = ctx.measureText(s).width;
    const u = eo(ent(0, 0, 1)); const x = 540 - w / 2 - 34, y = 196;
    ctx.save(); ctx.fillStyle = 'rgba(0,0,0,0.86)'; HOJA.rr(ctx, x, y, w + 68, 98, 14); ctx.fill();
    ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center'; ctx.fillText(s, 540, y + 71); ctx.restore();
    if (w + 68 > 1000) avisos.push('rótulo ancho ' + s);
  }
  function logoFicha(ctx, cx, cy, lado, alfa) {   // logo original sobre su fondo #FEFEFE, esquinas 11 % (≤ 12 %)
    if (alfa <= 0) return; ctx.save(); ctx.globalAlpha = alfa; ctx.shadowColor = 'rgba(0,0,0,0.35)'; ctx.shadowBlur = 18;
    HOJA.rr(ctx, cx - lado / 2, cy - lado / 2, lado, lado, lado * 0.11); ctx.fillStyle = '#FEFEFE'; ctx.fill(); ctx.shadowBlur = 0; ctx.clip();
    ctx.drawImage(A.img['logo'], cx - lado / 2, cy - lado / 2, lado, lado); ctx.restore();
  }
  // ---------- qué imágenes necesita cada cuadro
  const S = () => A.src;
  function necesita(g) {
    const p = n => String(n).padStart(4, '0'); const r = { logo: A.logo };
    if (en2(g, 't9') || en2(g, 't10')) r.v = `${S()}/7859/${p(n7859(g))}.png`;
    if (en2(g, 't10')) r.fill = `${S()}/7859fill/${p(n7859(g))}.png`;
    if (en2(g, 't11')) { r.v = `${S()}/879/${p(134 + g - T2.t11[0])}.png`; r.fill = `${S()}/879fill/${p(134 + g - T2.t11[0])}.png`; }
    if (en2(g, 't12')) r.v = `${S()}/32807/${p(50 + g - T2.t12[0])}.png`;
    if (en2(g, 't13')) r.v = `${S()}/40971/${p(0 + g - T2.t13[0])}.png`;
    if (en2(g, 't14')) { r.v = `${S()}/7859/${p(nCTA(g))}.png`; r.fill = `${S()}/7859fill/${p(nCTA(g))}.png`; }
    return r;
  }
  let OFF = null; function lienzo() { if (!OFF) { const cv = document.createElement('canvas'); cv.width = 2160; cv.height = 3840; OFF = { cv, ctx: cv.getContext('2d') }; } return OFF; }
  // ---------- dibujo
  function dibujar(ctx, g) {
    avisos.length = 0;
    if (g <= T2.t8[1]) {
      const f = viejo(g); HOJA.dibujar(ctx, estadoHoja(f)); dedoHoja(ctx, f, g); encabezado(ctx, f, 1);
    } else if (en2(g, 't9')) {
      HOJA.dibujar(ctx, estado9(g)); dedo9(ctx, g); encabezado(ctx, 400, 1);          // «¿Cuál tocás?» sigue arriba
    } else if (en2(g, 't10')) {    // tramo 10: el círculo se abre a la ventana (15 cuadros) y la espalda queda en pantalla
      const t0 = T2.t10[0]; const u = eio(ent(g, t0, t0 + 14)); const n = n7859(g);
      ctx.drawImage(A.img.fill, 0, 0, 1080, 1920);
      const a = 1 - eo(ent(g, t0, t0 + 6));
      if (a > 0) { const o = lienzo(); o.ctx.setTransform(2, 0, 0, 2, 0, 0); o.ctx.clearRect(0, 0, 1080, 1920); HOJA.dibujar(o.ctx, estado9(G9.fin)); encabezado(o.ctx, 400, 1);
        ctx.save(); ctx.globalAlpha = a; ctx.drawImage(o.cv, 0, 0, 1080, 1920); ctx.restore(); }
      const Yav = HOJA.Y(HOJA.AV_Y), r0 = HOJA.D(HOJA.AV_R) * ZF;
      const [sx0, sy0, sw0, sh0] = u < 1 ? recorte7859(Math.min(n, 119)) : [X10, 0, 2337, 2160];
      const sx = lerp(sx0, X10, u), sy = lerp(sy0, 0, u), sw = lerp(sw0, 2337, u), sh = lerp(sh0, 2160, u);
      const dw = lerp(2 * r0, VEN52.w, u), dh = lerp(2 * r0, VEN52.h, u), dx = 540 - dw / 2, dy = lerp(Yav - r0, VEN52.y, u);
      ventana(ctx, A.img.v, sx, sy, sw, sh, dx, dy, dw, dh, lerp(r0, 0, u));
    } else if (en2(g, 't11')) {
      ctx.drawImage(A.img.fill, 0, 0, 1080, 1920); ventana(ctx, A.img.v, 0, 0, 1920, 1080, 0, (1920 - 608) / 2, 1080, 608);
      rotulo(ctx, FINALES[0][2]);
    } else if (en2(g, 't12') || en2(g, 't13')) {
      ctx.drawImage(A.img.v, 0, 0, 1080, 1920); rotulo(ctx, en2(g, 't12') ? FINALES[1][2] : FINALES[2][2]);
    } else {                      // tramo 14: CTA. «El lunes, jugá la tuya.» y el logo entran con la segunda frase de v14
      const n = nCTA(g), t0 = T2.t14[0], t2 = 821;
      ctx.drawImage(A.img.fill, 0, 0, 1080, 1920); ventana(ctx, A.img.v, X14(n), 0, 2337, 2160, 0, VEN52.y, VEN52.w, VEN52.h);
      const gr = ctx.createLinearGradient(0, 120, 0, 480); gr.addColorStop(0, 'rgba(0,0,0,0.5)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = gr; ctx.fillRect(0, 0, 1080, 480);   // cielo claro: blanco con degradé oscuro suave (CLAUDE.md, 06 §4)
      textoSombra(ctx, 'El sábado, hinchá.', 540, 318, 68, '#ffffff', 700, 'InterDisplay', eo(ent(g, t0 - 1, t0 + 2)));
      textoSombra(ctx, 'El lunes, jugá la tuya.', 540, 412, 68, '#ffffff', 700, 'InterDisplay', eo(ent(g, t2 - 1, t2 + 2)));
      logoFicha(ctx, 540, 1556, 120, eo(ent(g, t2, t2 + 4)));
    }
    return avisos.slice();
  }
  return { N, T: T2, iniciar: a => { A = a; }, necesita, dibujar };
})();
