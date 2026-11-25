// Hoja reconstruida de la función «elegir equipo» de Instagram (IGLIB-1 e IGLIB-2). Canvas, coordenadas de la captura
// IMG_5535 (1170 px de ancho) llevadas al cuadro 1080×1920 con escala S y origen YS (borde superior de la hoja).
// Colores medidos en la captura (25/11/2026): fondo #0b1014, hoja #181c1f, tarjeta #2a3036, naranja #b74a00 (botón,
// borde de 6 px de la tarjeta elegida y punto activo), texto del botón #ffffff, blanco de títulos #f8f9f9, gris de textos
// y tirador #a0a9b5, punto inactivo y divisor #24292e. Tipografía sustituta: Inter. Sin contadores ni avatares de amigos
// (06 §1), sin usuario, barra de estado, notas ni la foto de la captura; foto de perfil = círculo gris liso.
'use strict';
const HOJA = (() => {
  const C = { fondo: '#0b1014', hoja: '#181c1f', tarjeta: '#2a3036', naranja: '#b74a00', btnTxt: '#ffffff',
    blanco: '#f8f9f9', gris: '#a0a9b5', inactivo: '#24292e', perfil: '#4b525a',
    celeste: '#c7def8',   // cursiva de PRODUCTO/blanca_espalda_estudio.jpg (P3→sRGB), normalizada al blanco de la remera
    marino: '#0f2747' };
  const L = { S: 0.78, YS: 452 };
  const X = x => 540 + (x - 585) * L.S, Y = y => L.YS + (y - 648) * L.S, D = v => v * L.S;
  const SHIFT = 61;                     // contenido de tarjeta centrado al quitar contadores y avatares (06 §1)
  const PITCH = 702, CARD_W = 660, CARD_TOP = 1114, CARD_BOT = 1953, CARD_R = 75, BORDE = 6;
  const AV_Y = 1390 + SHIFT, AV_R = 144, BADGE = [96, 94], BADGE_R = 48;
  const N1 = 1628 + SHIFT, N2 = 1700 + SHIFT;
  const lerp = (a, b, t) => a + (b - a) * t, clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
  const mix = (a, b, t) => { const p = hex(a), q = hex(b); return `rgb(${p.map((v, i) => Math.round(lerp(v, q[i], t))).join(',')})`; };
  function rr(ctx, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2); ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }
  // tamaño de letra en px de captura (medido por altura x / mayúscula en IMG_5535, Inter: x 0,546 em, mayúscula 0,727 em)
  const F = { conm: 36, titulo: 60.5, sub: 35.7, nombre: 60.5, cuenta: 44, boton: 42.3, chica: 35.7 };
  const font = (peso, px) => `${peso} ${D(px)}px Inter`;
  function texto(ctx, s, x, y, peso, px, color, ls = 0, align = 'center') {
    ctx.font = font(peso, px); ctx.fillStyle = color; ctx.textAlign = align; ctx.textBaseline = 'alphabetic';
    ctx.letterSpacing = ls ? `${D(ls)}px` : '0px'; ctx.fillText(s, x, y); ctx.letterSpacing = '0px';
  }
  // pelota de la insignia: base + pentágono central + cinco parches cortados por el borde (patrón de la captura)
  function pelota(ctx, cx, cy, r, base, parche) {
    ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.clip(); ctx.fillStyle = base; ctx.fillRect(cx - r, cy - r, 2 * r, 2 * r);
    const pent = (x, y, rad, rot) => { ctx.beginPath(); for (let k = 0; k < 5; k++) { const a = rot + k * 2 * Math.PI / 5; ctx[k ? 'lineTo' : 'moveTo'](x + rad * Math.cos(a), y + rad * Math.sin(a)); } ctx.closePath(); ctx.fill(); };
    ctx.fillStyle = parche; const rot = -Math.PI / 2; pent(cx, cy, r * 0.36, rot);
    ctx.strokeStyle = parche; ctx.lineWidth = r * 0.07;
    for (let k = 0; k < 5; k++) {
      const a = rot + k * 2 * Math.PI / 5; const vx = cx + r * 0.36 * Math.cos(a), vy = cy + r * 0.36 * Math.sin(a);
      const ox = cx + r * 0.98 * Math.cos(a), oy = cy + r * 0.98 * Math.sin(a);
      ctx.beginPath(); ctx.moveTo(vx, vy); ctx.lineTo(cx + r * 0.72 * Math.cos(a), cy + r * 0.72 * Math.sin(a)); ctx.stroke();
      pent(ox, oy, r * 0.32, a + Math.PI);
    }
    ctx.restore();
  }
  const EQUIPOS = [
    { lineas: ['Club Estudiantes de', 'La Plata'], pelota: ['#d1141d', '#0d0d0d'] },
    { lineas: ['SE Palmeiras'], pelota: ['#1d8a3f', '#f4f4f4'] },          // 06 §2: mismo patrón en verde y blanco
    { lineas: ['Vos'], sub: 'Tu propia final', propia: true },
  ];
  // e: estado. c = posición del carrusel; oculta = desplazamiento extra de la tercera tarjeta (px captura); sel[i] y
  // brillo[i] por tarjeta; borde3 = color del borde de la tarjeta 3; foto3(ctx, cx, cy, r) dibuja el video del círculo.
  function tarjeta(ctx, i, cx, e) {
    const eq = EQUIPOS[i]; const x = X(cx - CARD_W / 2), y = Y(CARD_TOP), w = D(CARD_W), h = D(CARD_BOT - CARD_TOP);
    if (x > 1080 || x + w < 0) return;
    rr(ctx, x, y, w, h, D(CARD_R)); ctx.fillStyle = C.tarjeta; ctx.fill();
    const b = e.brillo?.[i] || 0;
    if (b > 0) { ctx.save(); rr(ctx, x, y, w, h, D(CARD_R)); ctx.clip(); ctx.fillStyle = `rgba(255,255,255,${0.13 * b})`; ctx.fillRect(x, y, w, h); ctx.restore();
      ctx.save(); ctx.shadowColor = `rgba(255,255,255,${0.35 * b})`; ctx.shadowBlur = D(60); rr(ctx, x, y, w, h, D(CARD_R)); ctx.strokeStyle = `rgba(255,255,255,${0.10 * b})`; ctx.lineWidth = D(3); ctx.stroke(); ctx.restore(); }
    const s = e.sel?.[i] || 0;
    if (s > 0.001) { ctx.save(); ctx.globalAlpha = s; rr(ctx, x + D(BORDE / 2), y + D(BORDE / 2), w - D(BORDE), h - D(BORDE), D(CARD_R - BORDE / 2));
      ctx.strokeStyle = eq.propia ? C.celeste : C.naranja; ctx.lineWidth = D(BORDE); ctx.stroke(); ctx.restore(); }
    const ax = X(cx), ay = Y(AV_Y), ar = D(AV_R);
    if (eq.propia && e.foto3) { ctx.save(); ctx.beginPath(); ctx.arc(ax, ay, ar, 0, 7); ctx.clip(); e.foto3(ctx, ax, ay, ar); ctx.restore(); }
    else { ctx.beginPath(); ctx.arc(ax, ay, ar, 0, 7); ctx.fillStyle = C.perfil; ctx.fill(); }
    if (eq.pelota) { const bx = X(cx + BADGE[0]), by = Y(AV_Y + BADGE[1]);
      ctx.beginPath(); ctx.arc(bx, by, D(BADGE_R), 0, 7); ctx.fillStyle = C.hoja; ctx.fill(); pelota(ctx, bx, by, D(BADGE_R - 6), ...eq.pelota); }
    if (!e.sinNombres) {                     // IGLIB-2: vistas con zoom sin nombres de club (05 tramo 3)
      eq.lineas.forEach((l, k) => texto(ctx, l, X(cx), Y(k ? N2 : N1), 700, F.nombre, C.blanco));
      if (eq.sub) texto(ctx, eq.sub, X(cx), Y(N2), 400, F.cuenta, C.gris);
    }
  }
  function dibujar(ctx, e) {
    ctx.save();
    ctx.fillStyle = C.fondo; ctx.fillRect(0, 0, 1080, 1920);
    if (e.zoom && e.zoom.z !== 1) { const { z, px, py } = e.zoom; ctx.translate(px, py); ctx.scale(z, z); ctx.translate(-px, -py); }
    // hoja
    rr(ctx, -2, Y(648), 1084, 1920 - Y(648) + 400, D(46)); ctx.fillStyle = C.hoja; ctx.fill();
    rr(ctx, X(534), Y(693), D(101), D(6), D(3)); ctx.fillStyle = C.gris; ctx.fill();
    texto(ctx, 'CONMEBOL LIBERTADORES', 540, Y(808), 400, F.conm, C.gris, 1.4);
    texto(ctx, '¿Quién alcanzará la Gloria Eterna?', 540, Y(886), 700, F.titulo, C.blanco, -0.6);
    ['Tu selección se muestra en tu foto del perfil y te permite', 'acceder a un espacio para fans. Ambos permanecen hasta', 'que finaliza el evento.']
      .forEach((l, k) => texto(ctx, l, 540, Y(948 + 43 * k), 400, F.sub, C.gris, 0.25));
    // carrusel
    const c = e.c || 0;
    for (let i = 0; i < 3; i++) {
      if (i === 2 && !e.tercera) continue;
      const cx = 585 + (i - c) * PITCH + (i === 2 ? (e.oculta || 0) : 0); tarjeta(ctx, i, cx, e);
    }
    // puntos de paginación
    const n3 = e.puntos3 || 0;              // 0 → dos puntos, 1 → tres puntos
    const pos = [[558.5, 532.5], [610.5, 584.5], [662.5, 636.5]];
    for (let i = 0; i < 3; i++) {
      const a = i === 2 ? n3 : 1; if (a <= 0) continue;
      const px = lerp(pos[i][0], pos[i][1], n3); const w = clamp(1 - Math.abs(c - i));
      const act = i === 2 ? C.celeste : C.naranja;
      ctx.globalAlpha = a; ctx.beginPath(); ctx.arc(X(px), Y(1992.5), D(11), 0, 7); ctx.fillStyle = mix(C.inactivo, act, w); ctx.fill(); ctx.globalAlpha = 1;
    }
    ctx.fillStyle = C.inactivo; ctx.fillRect(0, Y(2102), 1080, D(2));
    // botón
    const bc = e.botonCeleste || 0, hund = e.hundido || 0;
    ctx.save(); const bx = X(48), by = Y(2151), bw = D(1074), bh = D(132);
    ctx.translate(bx + bw / 2, by + bh / 2); ctx.scale(1 - 0.035 * hund, 1 - 0.035 * hund); ctx.translate(-(bx + bw / 2), -(by + bh / 2));
    rr(ctx, bx, by, bw, bh, D(38)); ctx.fillStyle = mix(C.naranja, C.celeste, bc); ctx.fill();
    if (hund > 0) { ctx.fillStyle = `rgba(0,0,0,${0.18 * hund})`; ctx.fill(); }
    const ta = Math.max(0, 1 - 2 * bc), tb = Math.max(0, 2 * bc - 1);      // un texto sale antes de que entre el otro
    if (ta > 0) { ctx.globalAlpha = ta; texto(ctx, 'Elegir este equipo', 540, Y(2232), 600, F.boton, C.btnTxt); }
    if (tb > 0) { ctx.globalAlpha = tb; texto(ctx, 'GIVE HISTORY YOUR NAME.', 540, Y(2230), 700, F.boton, C.marino, 1.2); }
    ctx.globalAlpha = 1; ctx.restore();
    // letra chica (con subrayado naranja opcional en «puedes actualizarla cuando quieras», IGLIB-2)
    const l1 = 'Tus amigos pueden ver tu selección, y puedes actualizarla', l2 = 'cuando quieras.';
    texto(ctx, l1, 540, Y(2340), 400, F.chica, C.gris, 0.25); texto(ctx, l2, 540, Y(2384), 400, F.chica, C.gris, 0.25);
    if (e.subrayado > 0) {
      ctx.font = font(400, F.chica); ctx.letterSpacing = `${D(0.25)}px`;
      const w1 = ctx.measureText(l1).width, wPre = ctx.measureText('Tus amigos pueden ver tu selección, y ').width, w2 = ctx.measureText(l2).width;
      const wq = ctx.measureText('cuando quieras').width; ctx.letterSpacing = '0px';
      const x1 = 540 - w1 / 2 + wPre, x1e = 540 + w1 / 2, x2 = 540 - w2 / 2, x2e = x2 + wq;
      const u = e.subrayado; const L1 = x1e - x1, L2 = x2e - x2, tot = L1 + L2, hecho = u * tot;
      ctx.fillStyle = C.naranja;
      ctx.fillRect(x1, Y(2350), Math.min(L1, hecho), D(4));
      if (hecho > L1) ctx.fillRect(x2, Y(2394), hecho - L1, D(4));
    }
    ctx.restore();
  }
  // indicador de toque: círculo blanco al 60 % (06/encargo); p = presión 0..1, onda = anillo que se expande 0..1
  function dedo(ctx, x, y, alfa = 1, p = 0, onda = -1) {
    if (alfa <= 0) return; const r = 46 * (1 - 0.16 * p);
    ctx.save(); ctx.globalAlpha = alfa;
    ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fillStyle = 'rgba(255,255,255,0.6)'; ctx.shadowColor = 'rgba(0,0,0,0.35)'; ctx.shadowBlur = 14; ctx.fill();
    if (onda >= 0 && onda <= 1) { ctx.shadowBlur = 0; ctx.beginPath(); ctx.arc(x, y, r + 70 * onda, 0, 7); ctx.strokeStyle = `rgba(255,255,255,${0.5 * (1 - onda)})`; ctx.lineWidth = 4; ctx.stroke(); }
    ctx.restore();
  }
  return { C, L, X, Y, D, dibujar, dedo, rr, mix, PITCH, CARD_W, AV_Y, AV_R, N1, N2, CARD_TOP, CARD_BOT };
})();
