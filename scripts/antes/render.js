// Renderiza escena.html cuadro a cuadro con Chromium (Playwright): PNG 1080×1920 a 30 fps + eventos.json (línea de
// tiempo y golpes del aplauso, para el sonido). Fuentes e imágenes entran como data URL (sin depender de file://).
// Uso: node render.js SALIDA_DIR [desde_s] [hasta_s] [paso_cuadros]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const R = path.resolve(__dirname, '..', '..');
const out = process.argv[2]; const t0 = parseFloat(process.argv[3] || '0'); const t1 = process.argv[4] ? parseFloat(process.argv[4]) : null;
const paso = parseInt(process.argv[5] || '1');
fs.mkdirSync(out, { recursive: true });
const du = (p, mime) => `data:${mime};base64,` + fs.readFileSync(p).toString('base64');
const assets = {
  serif: du(path.join(R, 'scripts/fuentes/InstrumentSerif-Regular.ttf'), 'font/ttf'),
  serifIt: du(path.join(R, 'scripts/fuentes/InstrumentSerif-Italic.ttf'), 'font/ttf'),
  inter500: du('/usr/share/fonts/opentype/inter/Inter-Medium.otf', 'font/otf'),
  inter600: du('/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', 'font/otf'),
  caveat: du(path.join(R, 'scripts/fuentes/Caveat[wght].ttf'), 'font/ttf'),
  logo: du(path.join(R, 'TRABAJO/v4/assets/logo_recortado.png'), 'image/png'),
  remera: du(path.join(R, 'TRABAJO/v4/assets/remera_frente.png'), 'image/png'),
  espalda: du(path.join(R, 'TRABAJO/v4/assets/espalda_detalle.png'), 'image/png'),
};
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  pg.on('console', m => console.log('[pág]', m.text())); pg.on('pageerror', e => { console.error('ERROR', e); process.exit(1); });
  await pg.goto('file://' + path.join(__dirname, 'escena.html'));
  const info = await pg.evaluate(a => window.iniciar(a), assets);
  fs.writeFileSync(path.join(out, 'eventos.json'), JSON.stringify(info, null, 1));
  const fps = 30, n = Math.round(info.TL.dur * fps); const avisos = {};
  for (let i = Math.round(t0 * fps); i < (t1 ? Math.round(t1 * fps) : n); i += paso) {
    const r = await pg.evaluate(t => { const av = window.dibujar(t); return { av, png: document.getElementById('c').toDataURL('image/png') }; }, i / fps);
    if (r.av.length) avisos[i] = [...new Set(r.av)];
    fs.writeFileSync(path.join(out, `${String(i + 1).padStart(4, '0')}.png`), Buffer.from(r.png.split(',')[1], 'base64'));
  }
  fs.writeFileSync(path.join(out, 'avisos.json'), JSON.stringify(avisos, null, 1));
  console.log('cuadros listos; cuadros con avisos:', Object.keys(avisos).length);
  await b.close();
})();
