// IGLIB-1 «La tercera tarjeta» · v01 · 633 cuadros a 30 fps (21,10 s). Guion: 05_fede_guiones_G1.md con las
// correcciones de 06_roma_aprobacion_G1.md (sin contadores ni avatares, insignia verde y blanca, gancho ≥ 70 px,
// datos ≥ 56 px). Compositor de todo el cuadro: hoja reconstruida (hoja.js), video de cada tramo y textos.
'use strict';
const ESCENA = (() => {
  const N = 633;
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
  const T = { t1: [0, 44], t2: [45, 86], t3: [87, 131], t4: [132, 167], t5: [168, 203], t6: [204, 248], t7: [249, 308],
    t8: [309, 344], t9: [345, 434], t10: [435, 449], t11: [450, 488], t12: [489, 527], t13: [528, 563], t14: [564, 632] };
  const en = (f, t) => f >= T[t][0] && f <= T[t][1];
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
      botonCeleste: ent(f, 350, 354), hundido: kf(f, [[425, 0], [427, 1, eo], [431, 1], [434, 0.3]]), foto3: f >= 345 ? foto3(f) : null };
  }
  // ---------- video en el círculo de la tarjeta 3: IMG_7859 0,50–3,50 (cuadros 15–104), recorte que sigue «ROCCÉ»
  function recorte7859(n) { const v = A.track[n]; const side = v.ws * 1.58; return [v.cxs + v.ws * 0.05 - side / 2, v.cys + v.ws * 0.24 - side / 2, side, side]; }
  function foto3(f) { return (ctx, cx, cy, r) => { const n = 15 + (f - 345); const im = A.img['v']; const [sx, sy, sw, sh] = recorte7859(n);
    ctx.drawImage(im, sx, sy, sw, sh, cx - r, cy - r, 2 * r, 2 * r); }; }
  function dedoHoja(ctx, f) {
    const Y = HOJA.Y; const yc = 1150, yb = Y(2217);
    let x, y, a = 0, p = 0, onda = -1;
    const jit = k => Math.sin(f * 2.3 + k) * 4 + Math.sin(f * 3.7 + 2 * k) * 2;
    if (f <= 79) { x = 560; y = yc + 245; a = 1; p = kf(f, [[47, 0], [53, 1, eo], [68, 1], [74, 0]]); if (f >= 53 && f <= 68) onda = (f - 53) / 15; }
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
    else if (f <= 360) { [x, y] = kf(f, [[345, [930, yc]], [353, [120, yc], eo]]); a = kf(f, [[345, 0.5], [346, 1], [354, 1], [359, 0]]); p = f <= 353 ? 0.6 : 0; }
    else if (f <= 434) { [x, y] = kf(f, [[404, [700, yb + 120]], [424, [540, yb]]]); a = kf(f, [[404, 0], [410, 1], [434, 1]]);
      p = kf(f, [[424, 0], [426, 1, eo], [431, 1], [434, 0.4]]); if (f >= 426) onda = (f - 426) / 9; }
    // la vista de la hoja puede estar con zoom: el dedo sigue la misma transformación
    const z = estadoHoja(f).zoom; if (z.z && z.z !== 1 && x !== undefined) { x = z.px + (x - z.px) * z.z; y = z.py + (y - z.py) * z.z; }
    if (x !== undefined) HOJA.dedo(ctx, x, y, a, p, onda);
  }
  // ---------- ventanas de video con relleno desenfocado de la misma toma
  function ventana(ctx, im, sx, sy, sw, sh, dx, dy, dw, dh, r = 0) {
    ctx.save(); HOJA.rr(ctx, dx, dy, dw, dh, r); ctx.clip(); ctx.drawImage(im, sx, sy, sw, sh, dx, dy, dw, dh); ctx.restore();
  }
  const VEN52 = { w: 1080, h: 998, y: (1920 - 998) / 2 };      // ventana 52 % del alto
  const X10 = 698, X14 = 616;                                   // recortes fijos 2337×2160 centrados en la espalda
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
  function necesita(f) {
    const p = n => String(n).padStart(4, '0'); const r = { logo: A.logo };
    if (f >= 345 && f <= 449) r.v = `${S()}/7859/${p(15 + f - 345)}.png`;
    if (f >= 435 && f <= 449) r.fill = `${S()}/7859fill/${p(15 + f - 345)}.png`;
    if (en(f, 't11')) { r.v = `${S()}/879/${p(134 + f - 450)}.png`; r.fill = `${S()}/879fill/${p(134 + f - 450)}.png`; }
    if (en(f, 't12')) r.v = `${S()}/32807/${p(50 + f - 489)}.png`;
    if (en(f, 't13')) r.v = `${S()}/40971/${p(0 + f - 528)}.png`;
    if (en(f, 't14')) { r.v = `${S()}/7859/${p(180 + f - 564)}.png`; r.fill = `${S()}/7859fill/${p(180 + f - 564)}.png`; }
    return r;
  }
  let OFF = null; function lienzo() { if (!OFF) { const cv = document.createElement('canvas'); cv.width = 2160; cv.height = 3840; OFF = { cv, ctx: cv.getContext('2d') }; } return OFF; }
  // ---------- dibujo
  function dibujar(ctx, f) {
    avisos.length = 0;
    if (f <= 434) {
      HOJA.dibujar(ctx, estadoHoja(f)); dedoHoja(ctx, f); encabezado(ctx, f, 1);
    } else if (f <= 449) {         // tramo 10: el círculo se abre a la ventana; se va el encabezado
      const u = eio(ent(f, 435, 449)); const n = 15 + f - 345;
      ctx.drawImage(A.img.fill, 0, 0, 1080, 1920);
      const a = 1 - eo(ent(f, 435, 441));
      if (a > 0) { const o = lienzo(); o.ctx.setTransform(2, 0, 0, 2, 0, 0); o.ctx.clearRect(0, 0, 1080, 1920); HOJA.dibujar(o.ctx, estadoHoja(434)); encabezado(o.ctx, 434, 1);
        ctx.save(); ctx.globalAlpha = a; ctx.drawImage(o.cv, 0, 0, 1080, 1920); ctx.restore(); }
      const z = 1.08, Yav = HOJA.Y(HOJA.AV_Y), r0 = HOJA.D(HOJA.AV_R) * z;
      const [sx0, sy0, sw0, sh0] = recorte7859(n);
      const sx = lerp(sx0, X10, u), sy = lerp(sy0, 0, u), sw = lerp(sw0, 2337, u), sh = lerp(sh0, 2160, u);
      const dw = lerp(2 * r0, VEN52.w, u), dh = lerp(2 * r0, VEN52.h, u), dx = 540 - dw / 2, dy = lerp(Yav - r0, VEN52.y, u);
      ventana(ctx, A.img.v, sx, sy, sw, sh, dx, dy, dw, dh, lerp(r0, 0, u));
    } else if (en(f, 't11')) {
      ctx.drawImage(A.img.fill, 0, 0, 1080, 1920); ventana(ctx, A.img.v, 0, 0, 1920, 1080, 0, (1920 - 608) / 2, 1080, 608);
      rotulo(ctx, FINALES[0][2]);
    } else if (en(f, 't12') || en(f, 't13')) {
      ctx.drawImage(A.img.v, 0, 0, 1080, 1920); rotulo(ctx, en(f, 't12') ? FINALES[1][2] : FINALES[2][2]);
    } else {                      // tramo 14: CTA
      ctx.drawImage(A.img.fill, 0, 0, 1080, 1920); ventana(ctx, A.img.v, X14, 0, 2337, 2160, 0, VEN52.y, VEN52.w, VEN52.h);
      const gr = ctx.createLinearGradient(0, 120, 0, 480); gr.addColorStop(0, 'rgba(0,0,0,0.5)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = gr; ctx.fillRect(0, 0, 1080, 480);   // cielo claro: blanco con degradé oscuro suave (CLAUDE.md, 06 §4)
      textoSombra(ctx, 'El sábado, hinchá.', 540, 318, 68, '#ffffff', 700, 'InterDisplay', eo(ent(f, 563, 566)));
      textoSombra(ctx, 'El lunes, jugá la tuya.', 540, 412, 68, '#ffffff', 700, 'InterDisplay', eo(ent(f, 587, 590)));
      logoFicha(ctx, 540, 1556, 120, eo(ent(f, 588, 592)));
    }
    return avisos.slice();
  }
  return { N, T, iniciar: a => { A = a; }, necesita, dibujar };
})();
