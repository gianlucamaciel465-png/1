// IGLIB-2 «Nadie cambia» · v02 (con locución Firme 04, 10_roma_locucion_G1.1.md) · 528 cuadros a 30 fps (17,60 s), en loop.
// Guion: 05_fede_guiones_G1.md (IGLIB-2) con 06_roma_aprobacion_G1.md; línea de tiempo recalculada con la duración real
// de cada frase (voz/locucion.json). Compositor de todo el cuadro: hoja reconstruida (hoja.js), ventanas de video,
// preguntas y sellos. El último cuadro (527) es el encuadre exacto de c0 sin textos: el loop vuelve a «¿Cambiás?».
'use strict';
const ESCENA = (() => {
  const N = 528;
  let A = {};
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x)), lerp = (a, b, t) => a + (b - a) * t;
  const eio = x => (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2), eo = x => 1 - Math.pow(1 - x, 3), lin = x => x;
  function kf(f, keys, ease = eio) {
    if (f <= keys[0][0]) return keys[0][1];
    for (let i = 0; i < keys.length - 1; i++) { const [a, va] = keys[i], [b, vb] = keys[i + 1];
      if (f <= b) { const u = (keys[i + 1][2] || ease)(clamp((f - a) / (b - a))); return Array.isArray(va) ? va.map((v, j) => lerp(v, vb[j], u)) : lerp(va, vb, u); } }
    return keys[keys.length - 1][1];
  }
  const ent = (f, a, b) => clamp((f - a) / (b - a));
  // ---------- tramos (cuadros, inclusivos). Cada frase entra 1 cuadro después del corte; cada «No.» cae en la acción.
  const T = { t1: [0, 83], t2: [84, 138], t3: [139, 172], t4: [173, 226], t5: [227, 287], t6: [288, 351], t7: [352, 413],
    t8: [414, 453], t9: [454, 509], t10: [510, 527] };
  const en = (f, t) => f >= T[t][0] && f <= T[t][1];
  // fuentes por tramo: [carpeta, primer cuadro de origen]
  const SRC = { t2: ['8744', 148], t4: ['44451', 235], t5: ['876', 6], t6: ['608', 60], t7: ['4627', 287], t8: ['3375', 15], t9: ['4627', 349] };
  // ---------- textos exactos (05 + 10_roma_locucion)
  const PREG = { t2: ['¿Y si tu equipo', 'pierde el sábado?'], t3: ['¿Y si tu equipo', 'pierde el sábado?'], t4: ['¿Y si errás el tiro?'],
    t5: ['¿Y si te quiebran', 'el saque?'], t6: ['¿Y si nadie', 'te ve correr?'] };
  const SELLOS = [[145, 172, 'No cambio.'], [210, 226, 'No.'], [271, 287, 'No.'], [335, 351, 'No.'], [417, 453, 'Tampoco.']];
  // ---------- encuadre de c0: ×1,85 con pivote en la letra chica (×2,5 no deja leer la frase entera: desvío anotado; con
  // ×1,85 entran enteros «…y puedes actualizarla / cuando quieras.» y «Elegir este equipo», medidos con Inter).
  // Queda: borde inferior de la tarjeta 1, dos puntos, botón, «…y puedes actualizarla / cuando quieras.» subrayado.
  const ZC = { z: 1.85, px: 808, py: 2284 };
  const avisos = [];
  function textoSombra(ctx, s, x, y, px, color = '#ffffff', peso = 700, fam = 'InterDisplay', alfa = 1) {
    if (alfa <= 0) return;
    ctx.save(); ctx.globalAlpha = alfa; ctx.font = `${peso} ${px}px ${fam}`; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    const w = ctx.measureText(s).width; if (w > 984) avisos.push(`texto ancho ${Math.round(w)}: ${s}`);
    ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 16; ctx.shadowOffsetY = 3; ctx.fillStyle = color; ctx.fillText(s, x, y); ctx.restore();
  }
  function degradeArriba(ctx, alto, a) {
    if (a <= 0) return; const gr = ctx.createLinearGradient(0, 0, 0, alto);
    gr.addColorStop(0, `rgba(0,0,0,${0.62 * a})`); gr.addColorStop(0.6, `rgba(0,0,0,${0.35 * a})`); gr.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = gr; ctx.fillRect(0, 0, 1080, alto);
  }
  // ---------- hoja: estado del encuadre de c0 (tarjeta 1 elegida, subrayado completo, sin nombres)
  function estadoC0(sub = 1, zoom = ZC) { return { c: 0, sel: [1, 0, 0], brillo: [0, 0, 0], tercera: false, sinNombres: true, subrayado: sub, zoom }; }
  // posición de «actualizarla» (en coordenadas de la hoja) para el indicador de toque
  let PALABRA = null;
  function palabra(ctx) {
    if (PALABRA) return PALABRA; const S = HOJA.L.S, px = 35.7 * S;
    ctx.save(); ctx.font = `400 ${px}px Inter`; ctx.letterSpacing = `${0.25 * S}px`;
    const l1 = 'Tus amigos pueden ver tu selección, y puedes actualizarla', w1 = ctx.measureText(l1).width;
    const pre = ctx.measureText('Tus amigos pueden ver tu selección, y puedes ').width, wa = ctx.measureText('actualizarla').width;
    ctx.letterSpacing = '0px'; ctx.restore();
    PALABRA = { x: 540 - w1 / 2 + pre + wa / 2, y: HOJA.Y(2350) + 30 }; return PALABRA;
  }
  const aZoom = (p, z) => [z.px + (p[0] - z.px) * z.z, z.py + (p[1] - z.py) * z.z];
  function dedoC0(ctx, g, alfa = 1) {        // indicador sobre «actualizarla», con un temblor leve (duda)
    const P = palabra(ctx); let [x, y] = aZoom([P.x, P.y], ZC);
    const j = k => Math.sin(g * 2.3 + k) * 3 + Math.sin(g * 3.7 + 2 * k) * 1.5;
    if (g > 0 && g < T.t1[1]) { x += j(1); y += j(2) * 0.6; }
    HOJA.dedo(ctx, x, y, alfa, 0);
  }
  // ---------- fondo de las ventanas: la hoja vacía (gris de la hoja sobre el fondo de la app, tirador arriba)
  function fondoHoja(ctx) {
    const C = HOJA.C; ctx.fillStyle = C.fondo; ctx.fillRect(0, 0, 1080, 1920);
    HOJA.rr(ctx, -2, 250, 1084, 1800, 40); ctx.fillStyle = C.hoja; ctx.fill();
    HOJA.rr(ctx, 540 - 40, 276, 80, 6, 3); ctx.fillStyle = C.gris; ctx.fill();
  }
  const VEN = { w: 1000, h: 563, x: 40, y: 679, r: 34 };
  function ventana(ctx, im) {
    ctx.save(); HOJA.rr(ctx, VEN.x, VEN.y, VEN.w, VEN.h, VEN.r); ctx.clip(); ctx.drawImage(im, 0, 0, 1920, 1080, VEN.x, VEN.y, VEN.w, VEN.h); ctx.restore();
  }
  function pregunta(ctx, lineas, f0, g, y0 = 470) {
    const u = f0 <= 0 ? 1 : eo(ent(g, f0 - 1, f0 + 2)); const px = 68, lh = 80;
    const ys = lineas.length === 1 ? [y0 + lh / 2] : [y0, y0 + lh];
    lineas.forEach((l, k) => textoSombra(ctx, l, 540, ys[k] + 12 * (1 - u), px, '#ffffff', 700, 'InterDisplay', u));
  }
  // sello: placa marino con borde y letras celeste, girada, entra con golpe (1,45 → 0,97 → 1)
  function sello(ctx, s, g, f0, cy, px = 132) {
    const t = g - f0; if (t < 0) return; const C = HOJA.C;
    const sc = t <= 0 ? 1.45 : kf(t, [[0, 1.45], [3, 0.97, eo], [5, 1]]); const a = clamp((t + 1) / 2);
    const sh = t <= 4 ? Math.sin(t * 2.6) * (4 - t) * 1.6 : 0;
    ctx.save(); ctx.globalAlpha = a; ctx.translate(540 + sh, cy); ctx.rotate(-7 * Math.PI / 180); ctx.scale(sc, sc);
    ctx.font = `700 ${px}px InterDisplay`; const w = ctx.measureText(s).width, padx = 46, h = px * 1.18;
    if (w + 2 * padx > 1000) avisos.push('sello ancho ' + s);
    ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = 26; ctx.shadowOffsetY = 6;
    HOJA.rr(ctx, -w / 2 - padx, -h / 2, w + 2 * padx, h, 22); ctx.fillStyle = 'rgba(15,39,71,0.94)'; ctx.fill();
    ctx.shadowColor = 'transparent'; ctx.lineWidth = 8; ctx.strokeStyle = C.celeste; HOJA.rr(ctx, -w / 2 - padx + 12, -h / 2 + 12, w + 2 * padx - 24, h - 24, 14); ctx.stroke();
    ctx.fillStyle = C.celeste; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(s, 0, px * 0.04); ctx.restore();
  }
  function sellos(ctx, g, cy) { for (const [a, b, s] of SELLOS) if (g >= a && g <= b) sello(ctx, s, g, a, cy, s === 'Tampoco.' ? 140 : 132); }
  function logoFicha(ctx, cx, cy, lado, alfa) {   // logo original sobre su fondo #FEFEFE, esquinas 11 % (≤ 12 %)
    if (alfa <= 0) return; ctx.save(); ctx.globalAlpha = alfa; ctx.shadowColor = 'rgba(0,0,0,0.35)'; ctx.shadowBlur = 18;
    HOJA.rr(ctx, cx - lado / 2, cy - lado / 2, lado, lado, lado * 0.11); ctx.fillStyle = '#FEFEFE'; ctx.fill(); ctx.shadowBlur = 0; ctx.clip();
    ctx.drawImage(A.img.logo, cx - lado / 2, cy - lado / 2, lado, lado); ctx.restore();
  }
  // ---------- qué imágenes necesita cada cuadro
  function necesita(g) {
    const r = { logo: A.logo };
    for (const t of Object.keys(SRC)) if (en(g, t)) { const [d, a] = SRC[t]; r.v = `${A.src}/${d}/${String(a + g - T[t][0]).padStart(4, '0')}.png`; }
    return r;
  }
  // ---------- dibujo
  function dibujar(ctx, g) {
    avisos.length = 0;
    if (en(g, 't1')) {                              // APUESTA: letra chica subrayada, «¿Cambiás?»
      HOJA.dibujar(ctx, estadoC0()); dedoC0(ctx, g); degradeArriba(ctx, 700, 1);
      // debajo de la insignia (y 120–258) para que nada pase por detrás de las letras
      textoSombra(ctx, 'Instagram te deja', 540, 344, 72); textoSombra(ctx, 'cambiar de equipo.', 540, 428, 72);
      textoSombra(ctx, '¿Cambiás?', 540, 590, 128);
    } else if (en(g, 't3')) {                       // la hoja a ×1,6: arrastra, el punto 2 se enciende a medias, suelta
      const c = kf(g, [[139, 0], [145, 0.45, eo], [148, 0.45], [151, -0.04, eo], [154, 0.01], [156, 0]]);
      HOJA.dibujar(ctx, { c, sel: [clamp(1 - c * 2), clamp(c * 2) * 0.5, 0], brillo: [0, 0, 0], tercera: false, sinNombres: true, zoom: { z: 1.6, px: 540, py: 1990 } });   // insignia (y 589–709) debajo de la pregunta
      const [x, a] = [kf(g, [[139, 780], [145, 470, eo], [148, 470]]), kf(g, [[139, 0.7], [140, 1], [148, 1], [151, 0]])];
      HOJA.dedo(ctx, x, 800, a, 0.5);
      degradeArriba(ctx, 640, 1.5); pregunta(ctx, PREG.t3, -1, g); sellos(ctx, g, 1010);   // el sello cae sobre la tarjeta; el degradé tapa el borde de la bajada de la hoja
    } else if (en(g, 't2') || en(g, 't4') || en(g, 't5') || en(g, 't6')) {
      const t = ['t2', 't4', 't5', 't6'].find(t => en(g, t));
      fondoHoja(ctx); ventana(ctx, A.img.v); pregunta(ctx, PREG[t], T[t][0], g); sellos(ctx, g, 1420);
    } else if (en(g, 't7')) {                       // GRAN PREGUNTA sobre la Blanca en la roca (pantalla completa)
      ctx.drawImage(A.img.v, 0, 0, 1080, 1920); degradeArriba(ctx, 720, 1.3);   // espuma clara: blanco con degradé oscuro
      const u = eo(ent(g, T.t7[0] - 1, T.t7[0] + 2));
      textoSombra(ctx, '¿Y si lo tuyo', 540, 300 + 12 * (1 - u), 72, '#ffffff', 700, 'InterDisplay', u);
      textoSombra(ctx, 'todavía no arranca?', 540, 386 + 12 * (1 - u), 72, '#ffffff', 700, 'InterDisplay', u);
    } else if (en(g, 't8')) {                       // GIRO: la mano sostiene la Blanca de frente; «Tampoco.»
      ctx.drawImage(A.img.v, 0, 0, 1080, 1920); sellos(ctx, g, 1500);
    } else if (en(g, 't9')) {                       // CTA
      ctx.drawImage(A.img.v, 0, 0, 1080, 1920); degradeArriba(ctx, 720, 1.3);
      const u = eo(ent(g, T.t9[0] - 1, T.t9[0] + 2));
      textoSombra(ctx, 'Mandáselo al que', 540, 300, 72, '#ffffff', 700, 'InterDisplay', u);
      textoSombra(ctx, 'no afloja.', 540, 386, 72, '#ffffff', 700, 'InterDisplay', u);
      logoFicha(ctx, 540, 1745, 112, eo(ent(g, 470, 474)));
    } else {                                        // REENGANCHE: hoja entera ×1 → encuadre exacto de c0, sin textos
      const u = eio(ent(g, T.t10[0], T.t10[1]));
      const z = { z: lerp(1, ZC.z, u), px: ZC.px, py: ZC.py };
      HOJA.dibujar(ctx, estadoC0(eio(ent(g, 512, 525)), z));
      const P = palabra(ctx); const fin = aZoom([P.x, P.y], ZC);
      const [x, y] = kf(g, [[513, [fin[0] + 60, fin[1] + 260]], [527, fin]], eo);
      HOJA.dedo(ctx, x, y, kf(g, [[513, 0], [517, 1]]), 0);
      degradeArriba(ctx, 700, eio(ent(g, 517, 527)));   // el degradé de c0 ya está en c527: la costura solo suma los textos
    }
    return avisos.slice();
  }
  return { N, T, iniciar: a => { A = a; }, necesita, dibujar };
})();
