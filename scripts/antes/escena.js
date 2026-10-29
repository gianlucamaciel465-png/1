// ROCCE_ANTES_DEL_APLAUSO — escena animada por código (canvas 1080×1920, se renderiza cuadro a cuadro con Chromium).
// Dirección: papel claro con bruma fría, serif editorial (Instrument Serif) con cursivas puntuales, rótulos y CTA en
// sans discreta (Inter), figuras blancas con contorno grafito, celeste humo como acento de Roccé.
// Dos franjas de una misma composición: arriba EL APLAUSO (el resultado), abajo LO QUE HUBO ANTES (el proceso de la
// MISMA persona). El lápiz siempre toca la hoja (el trazo crece desde la punta); las hojas descartadas quedan a la vista.
// Producto y logo: archivos reales (recorte de la foto de frente, detalle de la espalda, logo sin fondo).
'use strict';
const W = 1080, H = 1920;
const PAPEL = '#EEECE7', GRAF = '#1D1E21', GRIS = '#6F7279', CEL = '#A6C0D3', CELO = '#5F86A3';
const BLANCO = '#FBFBFA';
let ctx, A = {};

// ---------- utilidades
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const seg = (t, a, b) => clamp((t - a) / (b - a));
const eio = x => (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const eo = x => 1 - Math.pow(1 - x, 3);
const ei = x => x * x * x;
const eback = x => { const c = 1.4; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
function kf(t, keys, ease = eio) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++) {
    const [t0, v0] = keys[i], [t1, v1] = keys[i + 1];
    if (t <= t1) { const u = ease(seg(t, t0, t1)); return Array.isArray(v0) ? v0.map((a, j) => lerp(a, v1[j], u)) : lerp(v0, v1, u); }
  }
  return keys[keys.length - 1][1];
}
const rad = d => d * Math.PI / 180;
const u2 = a => [Math.cos(a), Math.sin(a)];
const add = (p, q, s = 1) => [p[0] + q[0] * s, p[1] + q[1] * s];
const sub = (p, q) => [p[0] - q[0], p[1] - q[1]];
const len = v => Math.hypot(v[0], v[1]);
function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

// ---------- línea de tiempo (segundos). render.js la exporta para el sonido.
const TL = {
  dur: 15.0,
  voz: { v1: 0.20, v2: 1.90, v3: 3.95, v4: 5.62, v5: 8.30, v6: 11.55 },
  titulos: [
    { t0: -0.22, t1: 1.78, y: 250, size: 108, lineas: [[['Van', 0], ['a', 0], ['llamarlo', 0], ['suerte.', 1]]] },
    { t0: 1.86, t1: 3.88, y: 196, size: 100, lineas: [[['Vos', 0], ['sabés', 0], ['lo', 0], ['que', 0]], [['hubo', 0], ['antes.', 1]]] },
    { t0: 3.95, t1: 5.52, y: 250, size: 100, lineas: [[['Roccé', 0], ['te', 0], ['reconoce', 1], ['antes.', 0]]] },
    { t0: 8.22, t1: 10.92, y: 250, size: 108, lineas: [[['Proponé', 0], ['lo', 0], ['que', 0], ['viene.', 1]]] },
  ],
  cta1: [5.60, 8.16],
  // proceso (franja de abajo)
  dibujo1: [0.80, 2.20], mira: [2.20, 2.42], arranca: [2.42, 2.58], vuela1: [2.58, 2.98],
  dibujo2: [3.08, 3.92], firma: [4.22, 5.20], subraya: [5.20, 5.42],
  atras: [5.70, 6.35], adelante: [6.95, 7.45], levanta: [7.55, 8.20], tarjeta: [8.20, 9.30],
  chispa: [3.95, 4.62],
  cierre: [10.95, 11.55],
  aplausoFin: 2.3,
};

// ---------- fondo de papel (fijo) y luz que deriva
let fondo;
function crearFondo() {
  fondo = document.createElement('canvas'); fondo.width = W; fondo.height = H;
  const g = fondo.getContext('2d');
  g.fillStyle = PAPEL; g.fillRect(0, 0, W, H);
  let gr = g.createRadialGradient(W * 0.5, H * 0.42, 100, W * 0.5, H * 0.5, H * 0.75);
  gr.addColorStop(0, 'rgba(255,255,255,0.55)'); gr.addColorStop(0.55, 'rgba(232,236,239,0.25)'); gr.addColorStop(1, 'rgba(196,206,214,0.55)');
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  // grano de papel
  const im = g.getImageData(0, 0, W, H), d = im.data, r = rng(7);
  for (let i = 0; i < d.length; i += 4) { const n = (r() - 0.5) * 7; d[i] += n; d[i + 1] += n; d[i + 2] += n; }
  g.putImageData(im, 0, 0);
}
function luz(t, x0, y0, rr, a) {
  const x = x0 + 60 * Math.sin(t * 0.35), y = y0 + 40 * Math.cos(t * 0.27);
  const gr = ctx.createRadialGradient(x, y, 0, x, y, rr);
  gr.addColorStop(0, `rgba(255,255,255,${a})`); gr.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
}

// ---------- texto
const SERIF = (sz, it) => `${it ? 'italic ' : ''}${sz}px ISerif`;
function tituloKin(spec, t, dy = 0) {
  const { t0, t1 } = spec; if (t < t0 - 0.01 || t > t1 + 0.01) return;
  ctx.save(); ctx.textBaseline = 'alphabetic'; ctx.fillStyle = GRAF;
  let sz = spec.size;
  const medir = () => spec.lineas.map(l => l.reduce((s, [w, it], i) => { ctx.font = SERIF(sz, it); return s + ctx.measureText(w).width + (i ? sz * 0.24 : 0); }, 0));
  let ws = medir(); const mx = Math.max(...ws); if (mx > 960) { sz *= 960 / mx; ws = medir(); }
  let k = 0;
  spec.lineas.forEach((l, li) => {
    let x = (W - ws[li]) / 2; const y = spec.y + li * sz * 1.0 + dy;
    l.forEach(([w, it], i) => {
      ctx.font = SERIF(sz, it); const ww = ctx.measureText(w).width;
      const ta = t0 + k * 0.07; const a = eo(seg(t, ta, ta + 0.30)); const b = ei(seg(t, t1 - 0.24, t1));
      const al = a * (1 - b);
      if (al > 0.003) {
        const bl = (1 - a) * 14 + b * 10;
        ctx.filter = bl > 0.35 ? `blur(${bl.toFixed(1)}px)` : 'none';
        ctx.globalAlpha = al; ctx.fillText(w, x, y + (1 - a) * 18 - b * 14);
      }
      x += ww + sz * 0.24; k++;
    });
  });
  ctx.restore();
}
function sans(txt, x, y, sz, { peso = 600, color = GRAF, ls = 0, align = 'center', alpha = 1, blur = 0 } = {}) {
  ctx.save(); ctx.font = `${peso} ${sz}px InterX`; ctx.letterSpacing = `${ls}px`; ctx.fillStyle = color;
  ctx.globalAlpha = alpha; if (blur > 0.35) ctx.filter = `blur(${blur.toFixed(1)}px)`;
  const w = ctx.measureText(txt).width - ls; let xx = x;
  if (align === 'center') xx = x - w / 2; else if (align === 'right') xx = x - w;
  ctx.textBaseline = 'alphabetic'; ctx.fillText(txt, xx, y); ctx.restore(); return w;
}
function pill(txt, x, y, { fs = 22, bg = GRAF, fg = '#F3F2EE', ls = 3, align = 'left', alpha = 1, padx = 0.85, peso = 600, blur = 0 } = {}) {
  ctx.save(); ctx.font = `${peso} ${fs}px InterX`; ctx.letterSpacing = `${ls}px`;
  const tw = ctx.measureText(txt).width - ls; const h = fs * 1.85, w = tw + fs * padx * 2;
  let x0 = align === 'center' ? x - w / 2 : x;
  ctx.globalAlpha = alpha; if (blur > 0.35) ctx.filter = `blur(${blur.toFixed(1)}px)`;
  ctx.fillStyle = bg; ctx.beginPath(); ctx.roundRect(x0, y, w, h, h / 2); ctx.fill();
  ctx.fillStyle = fg; ctx.textBaseline = 'middle'; ctx.fillText(txt, x0 + fs * padx, y + h / 2 + fs * 0.04);
  ctx.restore(); return { w, h };
}

// ---------- figura (blanca, contorno grafito, volumen suave)
const FIG = { R: 34, w: 30, o: 6, torso: 150, brazo: 104, ante: 100, muslo: 94, pierna: 94 };
function polilinea(pts) { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); }
function desplazada(pts, d) {
  return pts.map((p, i) => {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
    const v = sub(b, a); const l = len(v) || 1; const n = [-v[1] / l, v[0] / l];
    const s = (n[0] + n[1] >= 0) ? 1 : -1;            // sombra hacia abajo/derecha (luz de arriba a la izquierda)
    return add(p, n, d * s);
  });
}
function miembro(pts, w, o, lejos = false) {
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  polilinea(pts); ctx.lineWidth = w + 2 * o; ctx.strokeStyle = GRAF; ctx.stroke();
  polilinea(pts); ctx.lineWidth = w; ctx.strokeStyle = lejos ? '#E4E5E8' : BLANCO; ctx.stroke();
  polilinea(desplazada(pts, w * 0.2)); ctx.lineWidth = w * 0.44; ctx.strokeStyle = 'rgba(28,34,48,0.075)'; ctx.stroke();
  ctx.restore();
}
function cabeza(c, R, o) {
  ctx.save(); ctx.beginPath(); ctx.arc(c[0], c[1], R + o, 0, 7); ctx.fillStyle = GRAF; ctx.fill();
  const g = ctx.createRadialGradient(c[0] - R * 0.35, c[1] - R * 0.4, R * 0.1, c[0], c[1], R * 1.05);
  g.addColorStop(0, '#FFFFFF'); g.addColorStop(0.7, '#F6F6F5'); g.addColorStop(1, '#E2E4E8');
  ctx.beginPath(); ctx.arc(c[0], c[1], R, 0, 7); ctx.fillStyle = g; ctx.fill(); ctx.restore();
}
function mano(p, r, o, lejos) {
  ctx.save(); ctx.beginPath(); ctx.arc(p[0], p[1], r + o, 0, 7); ctx.fillStyle = GRAF; ctx.fill();
  ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, 7); ctx.fillStyle = lejos ? '#E4E5E8' : BLANCO; ctx.fill(); ctx.restore();
}
function sombraPiso(x, y, rx) {
  ctx.save(); const g = ctx.createRadialGradient(x, y, 0, x, y, rx);
  g.addColorStop(0, 'rgba(25,28,36,0.20)'); g.addColorStop(1, 'rgba(25,28,36,0)');
  ctx.translate(x, y); ctx.scale(1, 0.16); ctx.translate(-x, -y);
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, rx, 0, 7); ctx.fill(); ctx.restore();
}
const avisos = [];
function ik(A_, T, l1, l2, flip, nombre) {
  let d = sub(T, A_), dist = len(d); const dmax = l1 + l2 - 0.5;
  if (dist > dmax) { avisos.push(`${nombre}: fuera de alcance ${dist.toFixed(1)} > ${dmax}`); d = [d[0] * dmax / dist, d[1] * dmax / dist]; dist = dmax; }
  const a = Math.atan2(d[1], d[0]);
  const b = Math.acos(clamp((l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist), -1, 1));
  const ang = a + (flip ? -b : b);
  return [add(A_, u2(ang), l1), add(A_, d)];
}
const LAPIZ = 50;                                            // de la mano a la punta
function lapiz(mano_, punta, s = 1) {
  // lápiz grafito con la madera afilada; va por delante de la mano (lo sostienen los dedos) y la punta toca la hoja
  ctx.save(); ctx.lineCap = 'round';
  const v = sub(punta, mano_), l = len(v), u = [v[0] / l, v[1] / l];
  const cola = add(mano_, u, -18 * s), madera = add(punta, u, -13 * s);
  ctx.beginPath(); ctx.moveTo(cola[0], cola[1]); ctx.lineTo(madera[0], madera[1]); ctx.lineWidth = 13 * s; ctx.strokeStyle = GRAF; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cola[0], cola[1]); ctx.lineTo(madera[0], madera[1]); ctx.lineWidth = 7 * s; ctx.strokeStyle = '#3A3D44'; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(madera[0] + u[1] * 4.5 * s, madera[1] - u[0] * 4.5 * s); ctx.lineTo(punta[0], punta[1]);
  ctx.lineTo(madera[0] - u[1] * 4.5 * s, madera[1] + u[0] * 4.5 * s); ctx.closePath(); ctx.fillStyle = '#D6C29C'; ctx.fill();
  ctx.lineWidth = 1.6 * s; ctx.strokeStyle = GRAF; ctx.stroke();
  ctx.beginPath(); ctx.arc(punta[0] - u[0] * 1.5 * s, punta[1] - u[1] * 1.5 * s, 2.4 * s, 0, 7); ctx.fillStyle = GRAF; ctx.fill();
  ctx.restore();
}

// figura de perfil mirando a la derecha (franja de abajo). P: {cad, incl, cabeza, manoN (o null), manoL, pieN, pieL, lapiz}
function figuraPerfil(P) {
  const { R, w, o } = FIG;
  const d = [Math.sin(rad(P.incl)), -Math.cos(rad(P.incl))];          // de la cadera al cuello
  const cuello = add(P.cad, d, FIG.torso), hombro = add(cuello, d, -16);
  const cab = add(add(cuello, d, R + 8), [Math.sin(rad(P.cabeza)) * 6, 0]);
  sombraPiso((P.pieN[0] + P.pieL[0]) / 2, 1004, 120);
  // brazo lejano y pierna lejana
  const [codoL, manoL] = ik(hombro, P.manoL, FIG.brazo, FIG.ante, true, 'mano lejana');
  miembro([hombro, codoL, manoL], w, o, true); mano(manoL, w * 0.56, o, true);
  const [rodL, pieL] = ik(P.cad, P.pieL, FIG.muslo, FIG.pierna, true, 'pie lejano');
  miembro([P.cad, rodL, pieL, add(pieL, [16, 0])], w, o, true);
  // torso
  miembro([P.cad, cuello], w * 1.2, o);
  const [rodN, pieN] = ik(P.cad, P.pieN, FIG.muslo, FIG.pierna, true, 'pie cercano');
  miembro([P.cad, rodN, pieN, add(pieN, [16, 0])], w, o);
  cabeza(cab, R, o);
  // brazo cercano (con lápiz)
  let mN;
  if (P.punta) {
    const dirL = u2(rad(P.angLapiz ?? 52));
    const objetivo = add(P.punta, dirL, -LAPIZ);
    const [codoN, manoN] = ik(hombro, objetivo, FIG.brazo, FIG.ante, false, 'mano con lápiz');
    mN = manoN;
    if (len(sub(manoN, objetivo)) > 1.5) avisos.push('el lápiz no toca la hoja');
    miembro([hombro, codoN, manoN], w, o);
    mano(manoN, w * 0.56, o);
    lapiz(manoN, add(manoN, dirL, LAPIZ));
  } else {
    const [codoN, manoN] = ik(hombro, P.manoN, FIG.brazo, FIG.ante, false, 'mano cercana');
    mN = manoN;
    miembro([hombro, codoN, manoN], w, o);
    mano(manoN, w * 0.56, o);
    if (P.conLapiz) lapiz(manoN, add(manoN, u2(rad(100)), LAPIZ));
  }
  return { cuello, hombro, cab, manoN: mN };
}
// figura de frente (franja de arriba)
function figuraFrente(P) {
  const { R, w, o } = FIG;
  const cuello = [P.cad[0], P.cad[1] - FIG.torso], hombro = [cuello[0], cuello[1] + 18];
  const cab = [cuello[0] + P.cabeza * 0.4, cuello[1] - R - 8 + P.inclina];
  sombraPiso(P.cad[0], P.piso + 4, 120);
  const pi = [P.cad[0] - 30, P.piso], pd = [P.cad[0] + 30, P.piso];
  const [ri, fi] = ik([P.cad[0] - 8, P.cad[1]], pi, FIG.muslo, FIG.pierna, true, 'f pie i');
  const [rd, fd] = ik([P.cad[0] + 8, P.cad[1]], pd, FIG.muslo, FIG.pierna, false, 'f pie d');
  miembro([[P.cad[0] - 8, P.cad[1]], ri, fi, add(fi, [-12, 0])], w, o);
  miembro([[P.cad[0] + 8, P.cad[1]], rd, fd, add(fd, [12, 0])], w, o);
  // brazo izquierdo, relajado
  const [ci, mi] = ik(hombro, P.manoI, FIG.brazo, FIG.ante, true, 'f mano i');
  miembro([hombro, ci, mi], w, o); mano(mi, w * 0.56, o);
  miembro([P.cad, cuello], w * 1.2, o);
  cabeza(cab, R, o);
  // brazo derecho: mano en el pecho
  const [cd, md] = ik(hombro, P.manoD, FIG.brazo, FIG.ante, false, 'f mano d');
  miembro([hombro, cd, md], w, o); mano(md, w * 0.56, o);
}

// ---------- hoja y trazos (coordenadas de hoja: 216 × 270)
const HOJA = [216, 270];
function camino(pts, ruido, semilla, paso = 2.0) {
  const r = rng(semilla); const out = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i], b = pts[i + 1], l = len(sub(b, a)), n = Math.max(2, Math.ceil(l / paso));
    for (let k = 0; k < n; k++) { const s = k / n; out.push([lerp(a[0], b[0], s), lerp(a[1], b[1], s)]); }
  }
  out.push(pts[pts.length - 1]);
  // ruido suave (temblor de mano), filtrado
  let ex = 0, ey = 0;
  return out.map(p => { ex = ex * 0.9 + (r() - 0.5) * ruido; ey = ey * 0.9 + (r() - 0.5) * ruido; return [p[0] + ex, p[1] + ey]; });
}
function largos(c) { const L = [0]; for (let i = 1; i < c.length; i++) L.push(L[i - 1] + len(sub(c[i], c[i - 1]))); return L; }
function estrellaPts(cx, cy, r, orden = [0, 2, 4, 1, 3, 0], rot = -90) {
  return orden.map(k => [cx + r * Math.cos(rad(rot + k * 72)), cy + r * Math.sin(rad(rot + k * 72))]);
}
const C_ESTRELLA = camino([...estrellaPts(108, 116, 58), add(estrellaPts(108, 116, 58)[1], [-4, -6])], 1.1, 11);
// primer intento: empieza bien y la tercera línea se va (temblor, zigzag y sale de la estrella)
const C_INTENTO1 = (() => {
  const e = estrellaPts(106, 118, 56);
  return camino([e[0], e[1], [e[1][0] - 20, e[1][1] - 34], [e[1][0] - 44, e[1][1] - 52], [e[1][0] - 30, e[1][1] - 66],
                 [e[1][0] - 62, e[1][1] - 70], [e[1][0] - 48, e[1][1] - 92], [e[1][0] - 84, e[1][1] - 96], [e[1][0] - 96, e[1][1] - 40]], 2.6, 5);
})();
const C_VIEJA1 = camino([...estrellaPts(100, 120, 50, [0, 2, 4, 1]).map((p, i) => [p[0] + (i % 2 ? 9 : -6), p[1] + (i === 2 ? 22 : 0)])], 2.2, 21);
const C_VIEJA1X = camino([[42, 60], [176, 196]], 1.6, 22), C_VIEJA1X2 = camino([[176, 60], [44, 190]], 1.6, 23);
const C_VIEJA2 = camino(Array.from({ length: 40 }, (_, i) => [110 + 52 * Math.cos(i * 0.21) + (i > 25 ? i - 25 : 0) * 2.5, 118 + 46 * Math.sin(i * 0.21)]), 1.8, 31);
const C_VIEJA2Z = camino([[60, 214], [92, 196], [118, 220], [150, 198], [176, 222]], 1.4, 32);
const C_SUBRAYA = camino([[34, 246], [80, 241], [130, 239], [168, 236], [186, 230]], 0.8, 41);
const FIRMA = { txt: 'TU NOMBRE', x: 30, base: 224, sz: 40 };

function trazo(c, p, ancho = 3.4) {
  if (p <= 0) return c[0];
  const L = largos(c), tot = L[L.length - 1], obj = tot * clamp(p);
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = '#26282C'; ctx.lineWidth = ancho;
  ctx.beginPath(); ctx.moveTo(c[0][0], c[0][1]); let punta = c[0];
  for (let i = 1; i < c.length; i++) {
    if (L[i] <= obj) { ctx.lineTo(c[i][0], c[i][1]); punta = c[i]; }
    else { const s = (obj - L[i - 1]) / (L[i] - L[i - 1]); punta = [lerp(c[i - 1][0], c[i][0], s), lerp(c[i - 1][1], c[i][1], s)]; ctx.lineTo(punta[0], punta[1]); break; }
  }
  ctx.stroke(); ctx.restore(); return punta;
}
function firma(p) {
  ctx.save(); ctx.font = `600 ${FIRMA.sz}px Caveat`; ctx.fillStyle = '#26282C'; ctx.textBaseline = 'alphabetic';
  const w = ctx.measureText(FIRMA.txt).width; const x1 = FIRMA.x + w * clamp(p);
  ctx.beginPath(); ctx.rect(FIRMA.x - 4, FIRMA.base - 60, Math.max(0, x1 - FIRMA.x + 4), 80); ctx.clip();
  ctx.fillText(FIRMA.txt, FIRMA.x, FIRMA.base); ctx.restore();
  return [x1, FIRMA.base - 13 + 9 * Math.sin(clamp(p) * Math.PI * 2 * 8.5)];
}
// dibuja una hoja (en coordenadas de escena) y su contenido; devuelve una función que pasa de hoja a escena
function hoja(x, y, rot, s, contenido, { sombra = 0.16, borde = true } = {}) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rad(rot)); ctx.scale(s, s);
  ctx.shadowColor = `rgba(20,24,32,${sombra})`; ctx.shadowBlur = 14 / s; ctx.shadowOffsetY = 4 / s;
  ctx.fillStyle = '#FDFDFB'; ctx.fillRect(-HOJA[0] / 2, -HOJA[1] / 2, HOJA[0], HOJA[1]);
  ctx.shadowColor = 'transparent';
  if (borde) { ctx.strokeStyle = 'rgba(29,30,33,0.22)'; ctx.lineWidth = 1.2 / s; ctx.strokeRect(-HOJA[0] / 2, -HOJA[1] / 2, HOJA[0], HOJA[1]); }
  ctx.translate(-HOJA[0] / 2, -HOJA[1] / 2);
  const r = contenido ? contenido() : null;
  ctx.restore();
  return r;
}
const aEscena = (x, y, rot, s, p) => { const q = [(p[0] - HOJA[0] / 2) * s, (p[1] - HOJA[1] / 2) * s]; const c = Math.cos(rad(rot)), sn = Math.sin(rad(rot)); return [x + q[0] * c - q[1] * sn, y + q[0] * sn + q[1] * c]; };
const contenidoFinal = () => { trazo(C_ESTRELLA, 1); firma(1); trazo(C_SUBRAYA, 1, 2.6); };

// ---------- caballete (coordenadas de la escena de abajo: caja 1020 × 1100, piso y = 1010)
const CAB = { x: 470, y: 520, w: 250, h: 312 };            // tablero
const PAD = { cx: 595, cy: 682, s: 1.0 };                  // centro de la hoja del block (216 × 270 a escala 1)
function caballete(t, hojasRestantes) {
  ctx.save(); ctx.lineCap = 'round';
  ctx.strokeStyle = GRAF; ctx.lineWidth = 9;
  ctx.beginPath(); ctx.moveTo(600, 500); ctx.lineTo(632, 1006); ctx.stroke();           // pata de atrás
  ctx.beginPath(); ctx.moveTo(500, 830); ctx.lineTo(462, 1008); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(690, 830); ctx.lineTo(732, 1008); ctx.stroke();
  ctx.fillStyle = '#D8D2C6'; ctx.strokeStyle = GRAF; ctx.lineWidth = 5;
  ctx.beginPath(); ctx.roundRect(CAB.x, CAB.y, CAB.w, CAB.h, 8); ctx.fill(); ctx.stroke();
  // espesor del block (hojas que quedan)
  for (let i = hojasRestantes; i >= 1; i--) {
    ctx.fillStyle = '#F4F3EF'; ctx.strokeStyle = 'rgba(29,30,33,0.35)'; ctx.lineWidth = 1.2;
    ctx.fillRect(PAD.cx - 108 + i * 1.2, PAD.cy - 135 + i * 2.2, 216, 270); ctx.strokeRect(PAD.cx - 108 + i * 1.2, PAD.cy - 135 + i * 2.2, 216, 270);
  }
  ctx.restore();
}
function bandeja() {
  ctx.save(); ctx.fillStyle = GRAF; ctx.beginPath(); ctx.roundRect(452, 828, 286, 14, 6); ctx.fill(); ctx.restore();
}
function broche() { ctx.save(); ctx.fillStyle = GRAF; ctx.beginPath(); ctx.roundRect(PAD.cx - 34, CAB.y + 6, 68, 18, 5); ctx.fill(); ctx.restore(); }
function etiquetaRocce(t) {
  // etiqueta de papel con el logo REAL, colgada del ángulo del tablero (está desde el primer intento)
  const brillo = seg(t, 4.55, 4.75) * (1 - seg(t, 5.4, 5.9));
  const ang = 3 * Math.sin(t * 1.7) + 9 * Math.exp(-3.2 * Math.max(0, t - 4.62)) * Math.sin(Math.max(0, t - 4.62) * 9) * (t > 4.62 ? 1 : 0);
  ctx.save(); ctx.translate(CAB.x + CAB.w - 8, CAB.y + 10); ctx.rotate(rad(ang));
  ctx.strokeStyle = GRAF; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(18, 40); ctx.stroke();
  ctx.translate(18, 40);
  if (brillo > 0) { const g = ctx.createRadialGradient(40, 50, 4, 40, 50, 120); g.addColorStop(0, `rgba(166,192,211,${0.65 * brillo})`); g.addColorStop(1, 'rgba(166,192,211,0)'); ctx.fillStyle = g; ctx.fillRect(-80, -70, 240, 240); }
  ctx.shadowColor = 'rgba(20,24,32,0.18)'; ctx.shadowBlur = 8; ctx.shadowOffsetY = 3;
  ctx.fillStyle = '#FDFDFB'; ctx.strokeStyle = GRAF; ctx.lineWidth = 2.5;
  ctx.beginPath(); ctx.roundRect(-6, 0, 92, 104, 10); ctx.fill(); ctx.shadowColor = 'transparent'; ctx.stroke();
  ctx.beginPath(); ctx.arc(40, 12, 4, 0, 7); ctx.fillStyle = GRAF; ctx.fill();
  const lh = 74, lw = lh * A.logo.width / A.logo.height; ctx.drawImage(A.logo, 40 - lw / 2, 22, lw, lh);
  ctx.restore();
}
// pila de hojas descartadas (quedan a la vista)
const PILA = [{ x: 838, y: 930, rot: -9, s: 0.6, c: () => { trazo(C_VIEJA1, 1, 3.6); trazo(C_VIEJA1X, 1, 3); trazo(C_VIEJA1X2, 1, 3); } },
              { x: 905, y: 942, rot: 12, s: 0.58, c: () => { trazo(C_VIEJA2, 1, 3.6); trazo(C_VIEJA2Z, 1, 3); } }];
const DESTINO1 = { x: 870, y: 928, rot: -17, s: 0.6 };

function etiquetaProceso(t, txt, t0, t1, x, y) {
  const a = eo(seg(t, t0, t0 + 0.22)) * (1 - ei(seg(t, t1 - 0.18, t1)));
  if (a <= 0.01) return;
  ctx.save(); ctx.globalAlpha = a;
  sans(txt, x, y, 30, { peso: 600, color: GRAF, ls: 4, align: 'left', blur: (1 - a) * 6 });
  ctx.strokeStyle = GRAF; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(x, y + 16); ctx.lineTo(x + 40 * a, y + 16); ctx.stroke();
  ctx.restore();
}
function chispaDibujo(p, s, a, glow = 1) {
  if (a <= 0.01) return;
  ctx.save(); ctx.globalAlpha = a;
  const g = ctx.createRadialGradient(p[0], p[1], 0, p[0], p[1], 70 * s);
  g.addColorStop(0, `rgba(166,192,211,${0.85 * glow})`); g.addColorStop(1, 'rgba(166,192,211,0)');
  ctx.fillStyle = g; ctx.fillRect(p[0] - 80 * s, p[1] - 80 * s, 160 * s, 160 * s);
  ctx.beginPath(); estrellaPts(p[0], p[1], 15 * s, [0, 1, 2, 3, 4], -90).forEach((q, i) => {
    const qi = [p[0] + 6.2 * s * Math.cos(rad(-90 + 36 + i * 72)), p[1] + 6.2 * s * Math.sin(rad(-90 + 36 + i * 72))];
    if (i === 0) ctx.moveTo(q[0], q[1]); else ctx.lineTo(q[0], q[1]); ctx.lineTo(qi[0], qi[1]);
  }); ctx.closePath(); ctx.fillStyle = GRAF; ctx.fill();
  ctx.restore();
}

// ---------- escena de abajo: lo que hubo antes
function estadoProceso(t) {
  const T = TL;
  // cuerpo
  const cadX = kf(t, [[0, 418], [T.atras[0], 418], [T.atras[1], 372], [T.adelante[0], 372], [T.adelante[1], 418], [T.levanta[0], 418], [T.levanta[1], 430]]);
  let incl = 14;
  if (t >= T.firma[0] - 0.3) incl = kf(t, [[T.firma[0] - 0.3, 14], [T.firma[0], 20], [T.firma[0] + 0.55, 27], [T.subraya[1], 27], [T.atras[1], 3], [T.adelante[0], 3], [T.adelante[1], 12], [T.levanta[1], 6]]);
  else if (t >= T.mira[0]) incl = kf(t, [[T.mira[0], 14], [T.mira[1], 10], [T.vuela1[0], 16], [T.vuela1[1], 12], [T.dibujo2[0], 15]]);
  const cabeza = (t > T.mira[0] && t < T.arranca[1]) ? -8 * Math.sin(Math.PI * seg(t, T.mira[0], T.arranca[1])) : 0;
  const caminando = (a, b) => t > a && t < b ? Math.sin(Math.PI * seg(t, a, b)) : 0;
  const levN = 14 * caminando(T.atras[0], T.atras[0] + 0.35) + 14 * caminando(T.adelante[0] + 0.25, T.adelante[1]);
  const levL = 14 * caminando(T.atras[0] + 0.3, T.atras[1]) + 14 * caminando(T.adelante[0], T.adelante[0] + 0.3);
  const cad = [cadX, 820 - 4 * (levN + levL) / 14 + (incl > 16 ? 3 : 0)];
  const pieN = [cadX + 22, 1002 - levN], pieL = [cadX - 24, 1002 - levL];
  return { cad, incl, cabeza, pieN, pieL };
}
// posición de la punta del lápiz (escena) según la acción
function escenaAbajo(t) {
  const T = TL;
  const hojaPad = (p) => aEscena(PAD.cx, PAD.cy, 0, 1, p);
  // fondo del piso
  ctx.save(); ctx.strokeStyle = 'rgba(29,30,33,0.28)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-200, 1010); ctx.lineTo(1300, 1010); ctx.stroke(); ctx.restore();
  // pila (las viejas siempre; la primera de este intento desde que cae)
  PILA.forEach(h => hoja(h.x, h.y, h.rot, h.s, h.c));
  const hojasRest = t < T.vuela1[0] ? 4 : 3;
  caballete(t, hojasRest);
  // hoja del block: primer intento → arrancada → vuela a la pila
  let vuelo = null;
  if (t < T.arranca[1]) {
    hoja(PAD.cx, PAD.cy, 0, 1, () => trazo(C_INTENTO1, eio(seg(t, T.dibujo1[0], T.dibujo1[1]))), { sombra: 0.08 });
  } else {
    // segunda hoja (limpia, del block) con la estrella y la firma
    if (t < T.levanta[1]) hoja(PAD.cx, PAD.cy, 0, 1, () => {
      trazo(C_ESTRELLA, eio(seg(t, T.dibujo2[0], T.dibujo2[1])));
      if (t >= T.firma[0]) firma(seg(t, T.firma[0], T.firma[1]));
      if (t >= T.subraya[0]) trazo(C_SUBRAYA, eio(seg(t, T.subraya[0], T.subraya[1])), 2.6);
    }, { sombra: 0.08 });
    // 1) tirón: la mano agarra la esquina de abajo a la izquierda y tira hacia abajo; la hoja se despega girando
    //    alrededor del ángulo de arriba a la derecha. 2) la suelta: vuela en arco y cae sobre la pila.
    const TIRON = T.vuela1[0] + 0.14;
    const k1 = eo(seg(t, T.vuela1[0], TIRON));
    const piv = [PAD.cx + 108, PAD.cy - 135];
    const rot1 = 9 * k1;                                                     // giro del tirón
    const c1 = add(rotarAlrededor([PAD.cx, PAD.cy], piv, rot1), [10 * k1, 26 * k1]);
    const v = eo(seg(t, TIRON, T.vuela1[1]));
    const asiento = Math.sin(seg(t, T.vuela1[1], T.vuela1[1] + 0.25) * Math.PI) * 4 * (t > T.vuela1[1] ? 1 : 0);
    const px = lerp(c1[0], DESTINO1.x, v), py = lerp(c1[1], DESTINO1.y, v) - Math.sin(v * Math.PI) * 90 - asiento;
    vuelo = [px, py, lerp(rot1, DESTINO1.rot, v) + Math.sin(v * Math.PI) * 10, lerp(1, DESTINO1.s, v)];
    vuelo.tiron = TIRON;
  }
  broche(); bandeja();
  etiquetaRocce(t);
  if (vuelo) hoja(vuelo[0], vuelo[1], vuelo[2], vuelo[3], () => trazo(C_INTENTO1, 1), { sombra: 0.2 });
  // figura
  const E = estadoProceso(t);
  let P = { cad: E.cad, incl: E.incl, cabeza: E.cabeza, pieN: E.pieN, pieL: E.pieL, manoL: [E.cad[0] - 30, E.cad[1] + 60], angLapiz: 52 };
  if (t >= T.dibujo1[0] && t < T.dibujo1[1]) {
    const L = largos(C_INTENTO1); const pnt = C_INTENTO1[Math.min(C_INTENTO1.length - 1, L.findIndex(v => v >= L[L.length - 1] * eio(seg(t, T.dibujo1[0], T.dibujo1[1]))))];
    P.punta = hojaPad(pnt);
  } else if (t < T.dibujo1[0]) {
    P.punta = hojaPad(add(C_INTENTO1[0], [0, -6 * (1 - seg(t, 0.55, T.dibujo1[0]))]));
  } else if (t < T.mira[1]) {
    P.punta = add(hojaPad(C_INTENTO1[C_INTENTO1.length - 1]), [-8 * seg(t, T.mira[0], T.mira[1]), -10 * seg(t, T.mira[0], T.mira[1])]);
  } else if (t < T.vuela1[1] + 0.1) {
    // agarra la esquina de abajo a la derecha y arranca la hoja (la mano acompaña el vuelo un tramo)
    const esquina = hojaPad([12, 258]);
    const sale = vuelo ? aEscena(vuelo[0], vuelo[1], vuelo[2], vuelo[3], [12, 258]) : esquina;
    if (t < T.arranca[1]) P.manoN = kf(t, [[T.mira[1], add(hojaPad(C_INTENTO1[C_INTENTO1.length - 1]), [-8, -10])], [T.arranca[1], esquina]]);
    else if (vuelo && t < vuelo.tiron) P.manoN = sale;                     // la mano sostiene la esquina durante el tirón
    else { const sol = vuelo ? aEscena(...hojaVuelo(T, vuelo.tiron), [12, 258]) : esquina;  // la suelta y sigue el gesto
           P.manoN = kf(t, [[vuelo ? vuelo.tiron : T.arranca[1], sol], [vuelo.tiron + 0.12, add(sol, [40, 18])], [T.vuela1[1] + 0.1, add(esquina, [16, 10])]]); }
    P.conLapiz = true;
  } else if (t < T.dibujo2[0]) {
    P.manoN = kf(t, [[T.vuela1[1] + 0.1, add(hojaPad([12, 258]), [16, 10])], [T.dibujo2[0], add(hojaPad(C_ESTRELLA[0]), [-20, -25])]]);
    P.conLapiz = true;
    if (t > T.dibujo2[0] - 0.12) { delete P.manoN; P.punta = add(hojaPad(C_ESTRELLA[0]), [0, -8 * (1 - seg(t, T.dibujo2[0] - 0.12, T.dibujo2[0]))]); }
  } else if (t < T.dibujo2[1]) {
    const L = largos(C_ESTRELLA); const q = eio(seg(t, T.dibujo2[0], T.dibujo2[1]));
    P.punta = hojaPad(C_ESTRELLA[Math.min(C_ESTRELLA.length - 1, L.findIndex(v => v >= L[L.length - 1] * q))]);
  } else if (t < T.firma[0]) {
    const a = hojaPad(C_ESTRELLA[C_ESTRELLA.length - 1]), b = hojaPad([FIRMA.x, FIRMA.base - 13]);
    const k = eio(seg(t, T.dibujo2[1], T.firma[0]));
    P.punta = add(lerp2(a, b, k), [0, -14 * Math.sin(Math.PI * k)]);
    P.levantado = Math.sin(Math.PI * k) > 0.05;
  } else if (t < T.firma[1]) {
    let pp; ctx.save(); ctx.font = `600 ${FIRMA.sz}px Caveat`; pp = firmaPunta(seg(t, T.firma[0], T.firma[1])); ctx.restore();
    P.punta = hojaPad(pp); P.angLapiz = 48;
  } else if (t < T.subraya[1] + 0.02) {
    const L = largos(C_SUBRAYA); const q = eio(seg(t, T.subraya[0], T.subraya[1]));
    P.punta = hojaPad(C_SUBRAYA[Math.min(C_SUBRAYA.length - 1, Math.max(0, L.findIndex(v => v >= L[L.length - 1] * q)))]); P.angLapiz = 48;
  } else if (t < T.levanta[0]) {
    // termina, se aleja a mirar, vuelve
    const finS = hojaPad(C_SUBRAYA[C_SUBRAYA.length - 1]);
    P.manoN = kf(t, [[T.subraya[1], add(finS, [-18, -24])], [T.subraya[1] + 0.35, [E.cad[0] + 40, E.cad[1] + 30]],
                     [T.adelante[1], [E.cad[0] + 40, E.cad[1] + 30]], [T.levanta[0], hojaPad([14, 16])]]);
    P.conLapiz = t < T.atras[0];
  } else if (t < T.levanta[1]) {
    // agarra la hoja firmada por el ángulo de arriba a la izquierda y la despega del block
    P.manoN = hojaPad([14, 16 - 40 * eio(seg(t, T.levanta[0] + 0.2, T.levanta[1]))]);
  } else {
    // la suelta hacia arriba (se vuelve tarjeta) y baja el brazo
    P.manoN = kf(t, [[T.levanta[1], hojaPad([14, -24])], [T.levanta[1] + 0.3, [E.cad[0] + 60, E.cad[1] - 300]], [T.tarjeta[1], [E.cad[0] + 40, E.cad[1] + 30]]]);
  }
  const fig = figuraPerfil(P);
  return { fig, hojaPad };
}
const lerp2 = (a, b, k) => [lerp(a[0], b[0], k), lerp(a[1], b[1], k)];
function rotarAlrededor(p, c, grados) { const a = rad(grados), d = sub(p, c); return [c[0] + d[0] * Math.cos(a) - d[1] * Math.sin(a), c[1] + d[0] * Math.sin(a) + d[1] * Math.cos(a)]; }
function hojaVuelo(T, tt) {   // posición de la hoja arrancada en el instante tt (mismo cálculo que en escenaAbajo)
  const TIRON = T.vuela1[0] + 0.14, k1 = eo(seg(tt, T.vuela1[0], TIRON)), piv = [PAD.cx + 108, PAD.cy - 135], rot1 = 9 * k1;
  const c1 = add(rotarAlrededor([PAD.cx, PAD.cy], piv, rot1), [10 * k1, 26 * k1]);
  return [c1[0], c1[1], rot1, 1];
}
function firmaPunta(p) {
  const w = ctx.measureText(FIRMA.txt).width;
  return [FIRMA.x + w * clamp(p), FIRMA.base - 13 + 9 * Math.sin(clamp(p) * Math.PI * 2 * 8.5)];
}

// ---------- escena de arriba: el aplauso (caja 1020 × 1000, piso y = 880)
// primer golpe en el cuadro 1 (t = 0,02 s): el aplauso y su sonido existen desde el comienzo
const PARES = [{ cx: 205, cy: 900, s: 1.7, f: 3.1, fase: 0.02 - 0.5 / 3.1, rot: 9 }, { cx: 745, cy: 915, s: 1.8, f: 3.5, fase: 0.17 - 0.5 / 3.5, rot: -8 }];
function sepPar(par, t) {
  const fin = TL.aplausoFin;
  const act = 1 - seg(t, fin - 0.25, fin + 0.35);
  const ph = (t - par.fase) * par.f;
  const ab = 0.5 + 0.5 * Math.cos(2 * Math.PI * ph);                // 0 = juntas (golpe)
  return { sep: lerp(60, 2 + 120 * Math.pow(ab, 0.8), act), baja: (1 - act) * 90 };
}
function golpesAplauso() {
  const out = [];
  PARES.forEach((par, i) => { for (let k = 0; ; k++) { const tk = par.fase + (k + 0.5) / par.f; if (tk > TL.aplausoFin + 0.1) break; if (tk >= 0) out.push({ t: +tk.toFixed(3), par: i }); } });
  return out.sort((a, b) => a.t - b.t);
}
function manoAplauso(lado, s) {
  // mano vista de costado, palma hacia el centro: dedos juntos hacia arriba, pulgar adelante, manga grafito
  ctx.save(); ctx.scale(lado * s, s); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  ctx.fillStyle = '#2A2C30'; ctx.beginPath(); ctx.roundRect(-30, 34, 60, 280, 16); ctx.fill();
  ctx.fillStyle = '#3A3C41'; ctx.fillRect(-30, 34, 60, 10);
  const forma = () => { ctx.beginPath(); ctx.moveTo(-28, 40); ctx.lineTo(-30, -30); ctx.quadraticCurveTo(-30, -66, -6, -70);
    ctx.quadraticCurveTo(26, -72, 28, -40); ctx.lineTo(30, 40); ctx.closePath(); };
  forma(); ctx.lineWidth = 11; ctx.strokeStyle = GRAF; ctx.stroke(); ctx.fillStyle = BLANCO; ctx.fill();
  ctx.save(); forma(); ctx.clip(); ctx.fillStyle = 'rgba(28,34,48,0.07)'; ctx.fillRect(4, -80, 40, 130); ctx.restore();
  ctx.lineWidth = 2.6; ctx.strokeStyle = 'rgba(29,30,33,0.45)';
  [-12, 2, 15].forEach(x => { ctx.beginPath(); ctx.moveTo(x, -64 + Math.abs(x) * 0.3); ctx.lineTo(x + 1, -34); ctx.stroke(); });
  // pulgar
  ctx.beginPath(); ctx.moveTo(22, 14); ctx.quadraticCurveTo(44, 2, 42, -22);
  ctx.lineWidth = 30; ctx.strokeStyle = GRAF; ctx.stroke(); ctx.lineWidth = 19; ctx.strokeStyle = BLANCO; ctx.stroke();
  ctx.restore();
}
function escenaArriba(t) {
  // luz de escenario
  const g = ctx.createRadialGradient(400, 420, 30, 420, 560, 520);
  g.addColorStop(0, 'rgba(255,255,255,0.85)'); g.addColorStop(0.6, 'rgba(255,255,255,0.18)'); g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g; ctx.fillRect(-200, -200, 1420, 1400);
  ctx.save(); ctx.strokeStyle = 'rgba(29,30,33,0.25)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-200, 880); ctx.lineTo(1300, 880); ctx.stroke(); ctx.restore();
  // la obra terminada, enmarcada (el mismo dibujo que se hace abajo)
  ctx.save(); ctx.shadowColor = 'rgba(20,24,32,0.22)'; ctx.shadowBlur = 18; ctx.shadowOffsetY = 6;
  ctx.fillStyle = GRAF; ctx.fillRect(522, 380, 236, 292); ctx.restore();
  hoja(640, 526, 0, 0.98, contenidoFinal, { sombra: 0, borde: false });
  // la misma figura, de frente: mano en el pecho, leve inclinación con los golpes
  const golpe = PARES.reduce((m, par) => Math.max(m, 1 - sepPar(par, t).sep / 122), 0);
  const nod = Math.sin(t * 2.2) * 2 + (t < TL.aplausoFin ? golpe * 3 : 0);
  figuraFrente({ cad: [360, 692], piso: 878, cabeza: 0, inclina: nod, manoI: [328, 752], manoD: [372, 598] });
  // manos del público (pocas), en primer plano
  PARES.forEach(par => {
    const { sep, baja } = sepPar(par, t);
    ctx.save(); ctx.translate(par.cx, par.cy + baja); ctx.rotate(rad(par.rot));
    ctx.save(); ctx.translate(-sep / 2 - 30 * par.s, 0); ctx.rotate(rad(10)); manoAplauso(1, par.s); ctx.restore();
    ctx.save(); ctx.translate(sep / 2 + 30 * par.s, 0); ctx.rotate(rad(-10)); manoAplauso(-1, par.s); ctx.restore();
    ctx.restore();
  });
}

// ---------- composición
function S(t) { return kf(t, [[0, 1920], [0.5, 1920], [1.6, 1100], [1.9, 1100], [3.9, 990], [5.5, 900], [7.9, 770], [8.2, 770], [8.95, 380]]); }
function panel(x, y, w, h, fill, fn) {
  if (h < 2) return;
  ctx.save(); ctx.beginPath(); ctx.roundRect(x, y, w, h, 26); ctx.fillStyle = fill; ctx.fill();
  ctx.clip(); fn(); ctx.restore();
  ctx.save(); ctx.beginPath(); ctx.roundRect(x, y, w, h, 26); ctx.strokeStyle = 'rgba(29,30,33,0.14)'; ctx.lineWidth = 1.5; ctx.stroke(); ctx.restore();
}
function composicionBandas(t, offY) {
  const s = S(t);
  // franja de arriba
  const uy = 380 + offY, uh = s - 380 - 10;
  if (uh > 2) {
    const gr = ctx.createLinearGradient(0, uy, 0, uy + uh); gr.addColorStop(0, '#E2E8EC'); gr.addColorStop(1, '#D3DBE1');
    panel(30, uy, 1020, uh, gr, () => {
      // encuadre: x 60–980, y 300–1000 de la escena (piso, obra, figura y manos), abajo contra el borde del panel
      const fw = lerp(900, 640, seg(uh, 800, 1400));            // panel alto (apertura): encuadre más cerrado
      const k = Math.min(1020 / fw, uh / 700), cxs = lerp(470, 455, seg(uh, 800, 1400));
      ctx.save(); ctx.translate(30 + 510 - cxs * k, uy + uh - 1000 * k); ctx.scale(k, k); escenaArriba(t); ctx.restore();
      pill('EL APLAUSO', 54, uy + 24, { fs: 25, ls: 3 });
    });
  }
  // franja de abajo (el proceso). En la parte B se achica hacia abajo para dejar lugar a la composición.
  const ly = Math.max(s, 380) + (uh > 2 ? 0 : 0) + offY, lh = 1890 - Math.max(s, 380) - (s > 382 ? 0 : 0);
  const pB = seg(t, 8.2, 9.0);
  panel(30, ly, 1020, lh, '#F6F4EF', () => {
    // encuadre: x 230–1010, y 440–1030 de la escena (figura, caballete, pila); en la parte B se achica abajo
    const kA = Math.min(1020 / 780, (lh - 50) / 590);
    const k = lerp(kA, 0.95, eio(pB));
    const ox = 30 + 510 - 620 * k, oy = ly + lh - 1030 * k - 8;
    ctx.save(); ctx.translate(ox, oy); ctx.scale(k, k);
    const r = escenaAbajo(t); escenaAbajo.ultimo = { k, ox, oy, r };
    ctx.restore();
    // rótulos del proceso (en coordenadas de pantalla, junto al tablero)
    const L = escenaAbajo.ultimo; const toS = p => [L.ox + p[0] * L.k, L.oy + p[1] * L.k];
    const ancla = toS([486, 486]);
    etiquetaProceso(t, 'PRIMER INTENTO', 0.85, 2.55, ancla[0], ancla[1]);
    etiquetaProceso(t, 'VOLVER', 2.62, 3.25, ancla[0], ancla[1]);
    etiquetaProceso(t, 'SEGUIR', 3.25, 4.25, ancla[0], ancla[1]);
    pill('LO QUE HUBO ANTES', 54, ly + 24, { fs: 25, ls: 3, alpha: 1 - seg(t, 8.3, 8.8) });
    // chispa: de la estrella terminada a la etiqueta de Roccé
    const c0 = toS(aEscena(PAD.cx, PAD.cy, 0, 1, [108, 34])), c1 = toS([CAB.x + CAB.w + 128, CAB.y + 60]);
    const q = eio(seg(t, TL.chispa[0], TL.chispa[1]));
    const pc = [lerp(c0[0], c1[0], q), lerp(c0[1], c1[1], q) - Math.sin(q * Math.PI) * 90 * L.k];
    const ach = eo(seg(t, TL.chispa[0] - 0.05, TL.chispa[0] + 0.15)) * (1 - eo(seg(t, TL.chispa[1], TL.chispa[1] + 0.35)));
    chispaDibujo(pc, L.k * 0.8, ach, 0.7);
  });
  // divisor
  if (uh > 2) { ctx.save(); ctx.strokeStyle = 'rgba(29,30,33,0.0)'; ctx.restore(); }
}

// ---------- parte B: la propuesta se integra a Founders Privée
const FOTO = { x: 110, y: 450, w: 760 };
function composicionPropuesta(t, offY) {
  const a = seg(t, 8.72, 9.25);
  if (a <= 0) return;
  const h = FOTO.w * A.espalda.height / A.espalda.width;
  const sube = (1 - eo(a)) * 70;
  ctx.save(); ctx.globalAlpha = eo(a);
  ctx.translate(0, offY + sube);
  ctx.shadowColor = 'rgba(20,24,32,0.25)'; ctx.shadowBlur = 40; ctx.shadowOffsetY = 16;
  ctx.beginPath(); ctx.roundRect(FOTO.x, FOTO.y, FOTO.w, h, 22); ctx.fillStyle = '#111'; ctx.fill();
  ctx.shadowColor = 'transparent'; ctx.save(); ctx.clip();
  const z = 1 + 0.03 * seg(t, 8.5, 11.0); const zx = FOTO.x + FOTO.w / 2, zy = FOTO.y + h / 2;
  ctx.translate(zx, zy); ctx.scale(z, z); ctx.translate(-zx, -zy);
  ctx.drawImage(A.espalda, FOTO.x, FOTO.y, FOTO.w, h); ctx.restore();
  pill('FOUNDERS PRIVÉE', FOTO.x + 24, FOTO.y + 24, { fs: 20, ls: 3, bg: 'rgba(246,244,239,0.92)', fg: GRAF });
  ctx.restore();
}
function tarjetaPropuesta(t, offY) {
  const T = TL; if (t < T.levanta[1] - 0.001) return;
  const L = escenaAbajo.ultimo; if (!L) return;
  const toS = p => [L.ox + p[0] * L.k, L.oy + p[1] * L.k + 0];
  const origen = toS([PAD.cx, PAD.cy - 40]);
  const q = eio(seg(t, T.tarjeta[0], T.tarjeta[1]));
  const hF = FOTO.w * A.espalda.height / A.espalda.width;
  const destino = [FOTO.x + FOTO.w + 10, FOTO.y + hF + 120 + offY];
  const x = lerp(origen[0], destino[0], q) + Math.sin(q * Math.PI) * 60;
  const y = lerp(origen[1], destino[1], q) - Math.sin(q * Math.PI) * 180;
  const s = lerp(L.k, 1.05, q), rot = lerp(0, 6, q) + Math.sin(q * Math.PI) * -10;
  const card = clamp(q * 2.2);                                     // hoja → tarjeta (esquinas, encabezado)
  ctx.save(); ctx.translate(x, y); ctx.rotate(rad(rot)); ctx.scale(s, s);
  ctx.shadowColor = `rgba(20,24,32,${0.12 + 0.16 * card})`; ctx.shadowBlur = 10 + 28 * card; ctx.shadowOffsetY = 4 + 10 * card;
  const hh = HOJA[1] + 56 * card;
  ctx.beginPath(); ctx.roundRect(-HOJA[0] / 2, -HOJA[1] / 2 - 56 * card, HOJA[0], hh, 4 + 16 * card); ctx.fillStyle = '#FDFDFB'; ctx.fill();
  ctx.shadowColor = 'transparent'; ctx.strokeStyle = `rgba(29,30,33,${0.22 + 0.2 * card})`; ctx.lineWidth = 1.4; ctx.stroke();
  if (card > 0.02) {
    ctx.globalAlpha = card;
    ctx.fillStyle = GRAF; ctx.beginPath(); ctx.roundRect(-HOJA[0] / 2, -HOJA[1] / 2 - 56 * card, HOJA[0], 46, [4 + 16 * card, 4 + 16 * card, 0, 0]); ctx.fill();
    ctx.font = '600 18px InterX'; ctx.letterSpacing = '3px'; ctx.fillStyle = '#F3F2EE'; ctx.textBaseline = 'middle';
    ctx.fillText('TU PROPUESTA', -HOJA[0] / 2 + 16, -HOJA[1] / 2 - 56 * card + 24);
    ctx.globalAlpha = 1;
  }
  ctx.translate(-HOJA[0] / 2, -HOJA[1] / 2); contenidoFinal();
  ctx.restore();
  // chispa que acompaña la tarjeta
  const ach = eo(seg(t, T.tarjeta[0], T.tarjeta[0] + 0.2)) * (1 - seg(t, 10.6, 10.95));
  chispaDibujo([x + 120 * s, y - 170 * s], 0.9, ach, 0.8);
}

// ---------- cierre
function cierre(t, offY) {
  const y0 = 1920 + offY; if (y0 > 1920) return;
  const lle = seg(t, TL.cierre[1] - 0.1, TL.cierre[1] + 0.5);
  // logo real sin fondo
  const lh = 190, lw = lh * A.logo.width / A.logo.height;
  ctx.drawImage(A.logo, 540 - lw / 2, y0 + 150, lw, lh);
  // título
  const ap = (d) => eo(seg(t, TL.cierre[1] + d, TL.cierre[1] + d + 0.35));
  ctx.save(); ctx.textBaseline = 'alphabetic'; ctx.fillStyle = GRAF;
  const piezas = [['Founders', 0], ['Privée', 1], ['·', 0], ['01/11/2026', 0]]; let sz = 76;
  const medir = () => piezas.reduce((s, [w, it], i) => { ctx.font = SERIF(sz, it); return s + ctx.measureText(w).width + (i ? sz * 0.24 : 0); }, 0);
  let tw = medir(); if (tw > 960) { sz *= 960 / tw; tw = medir(); }
  let x = (W - tw) / 2;
  piezas.forEach(([w, it], i) => { ctx.font = SERIF(sz, it); const a = ap(0.02 + i * 0.05); ctx.globalAlpha = a; ctx.filter = a < 0.97 ? `blur(${((1 - a) * 10).toFixed(1)}px)` : 'none'; ctx.fillText(w, x, y0 + 450); x += ctx.measureText(w).width + sz * 0.24; });
  ctx.restore();
  // la remera real (recorte de la foto), con sombra sobre el papel
  const tw2 = 860, th2 = tw2 * A.remera.height / A.remera.width;
  const z = 1 + 0.05 * eo(seg(t, TL.cierre[1] - 0.2, TL.dur)), fl = 7 * Math.sin((t - TL.cierre[1]) * 1.1);
  ctx.save(); const cx = 540, cy = y0 + 500 + th2 / 2 + fl;
  ctx.translate(cx, cy); ctx.scale(z, z); ctx.translate(-cx, -cy);
  ctx.shadowColor = 'rgba(20,24,32,0.28)'; ctx.shadowBlur = 46; ctx.shadowOffsetY = 22;
  ctx.drawImage(A.remera, 540 - tw2 / 2, y0 + 500 + fl, tw2, th2); ctx.restore();
  // CTA
  const c1 = ap(0.25), c2 = ap(0.4), c3 = ap(0.9);
  sans('ENTRÁ A LA COMUNIDAD', 540, y0 + 1435, 56, { peso: 600, ls: 3, alpha: c1, blur: (1 - c1) * 10 });
  pill('LINK EN BIO', 540, y0 + 1478, { fs: 34, ls: 3, bg: CEL, fg: GRAF, align: 'center', alpha: c2, blur: (1 - c2) * 8 });
  sans('GIVE HISTORY YOUR NAME.', 540, y0 + 1640, 24, { peso: 500, ls: 6, color: GRIS, alpha: 0.85 * c3 });
}

// ---------- CTA 1
function cta1(t, offY) {
  const [a0, a1] = TL.cta1; if (t < a0 - 0.01 || t > a1 + 0.01) return;
  const e = eo(seg(t, a0, a0 + 0.28)), s = ei(seg(t, a1 - 0.22, a1)), al = e * (1 - s);
  const e2 = eo(seg(t, a0 + 0.12, a0 + 0.4)) * (1 - s);
  sans('ENTRÁ A LA COMUNIDAD ROCCÉ', 540, 236 + offY + (1 - e) * 16 - s * 12, 52, { peso: 600, ls: 3, alpha: al, blur: (1 - e) * 12 + s * 10 });
  pill('LINK EN BIO', 540, 272 + offY + (1 - e2) * 14, { fs: 32, ls: 3, bg: CEL, fg: GRAF, align: 'center', alpha: e2, blur: (1 - e2) * 8 + s * 8 });
}

// ---------- cuadro
function dibujar(t) {
  avisos.length = 0;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.filter = 'none'; ctx.globalAlpha = 1;
  ctx.drawImage(fondo, 0, 0);
  luz(t, 540, 900, 900, 0.28);
  const off = -1920 * eio(seg(t, TL.cierre[0], TL.cierre[1]));
  const vel = Math.abs(1920 * (eio(seg(t + 1 / 60, TL.cierre[0], TL.cierre[1])) - eio(seg(t - 1 / 60, TL.cierre[0], TL.cierre[1]))) * 30);
  const desenf = Math.min(10, vel / 900);
  if (t < TL.cierre[1] + 0.001) {
    ctx.save(); if (desenf > 0.4) ctx.filter = `blur(${desenf.toFixed(1)}px)`;
    composicionBandas(t, off);
    composicionPropuesta(t, off);
    tarjetaPropuesta(t, off);
    TL.titulos.forEach(s => tituloKin(s, t, off));
    cta1(t, off);
    ctx.restore();
  }
  if (t >= TL.cierre[0]) { ctx.save(); if (desenf > 0.4) ctx.filter = `blur(${desenf.toFixed(1)}px)`; cierre(t, off); ctx.restore(); }
  return avisos.slice();
}

async function iniciar(assets) {
  const C = document.getElementById('c'); ctx = C.getContext('2d');
  const fuentes = [['ISerif', assets.serif, {}], ['ISerif', assets.serifIt, { style: 'italic' }], ['InterX', assets.inter500, { weight: '500' }],
                   ['InterX', assets.inter600, { weight: '600' }], ['Caveat', assets.caveat, { weight: '400 700' }]];
  for (const [n, u, d] of fuentes) { const f = new FontFace(n, `url(${u})`, d); await f.load(); document.fonts.add(f); }
  const img = u => new Promise((ok, mal) => { const i = new Image(); i.onload = () => ok(i); i.onerror = mal; i.src = u; });
  A.logo = await img(assets.logo); A.remera = await img(assets.remera); A.espalda = await img(assets.espalda);
  crearFondo();
  return { TL, golpes: golpesAplauso() };
}
window.iniciar = iniciar; window.dibujar = dibujar;
