// Renderiza escena.html cuadro a cuadro (Chromium + WebGL por software) a PNG 1080×1920, 30 fps, + eventos.json
// (línea de tiempo para el sonido). Sirve la escena y three.js por HTTP local (los módulos no cargan con file://).
// Uso: node render.js SALIDA_DIR [desde_s] [hasta_s]   ·   node render.js SALIDA_DIR --tiempos 0,2.5,7.3 (prueba)
// Necesita: npm install en esta carpeta (three 0.170.0) y el estampado real en TRABAJO/v5/post/estampado.png
// (scripts/cerca/arte_estampado.py).
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path');
const R = path.resolve(__dirname, '..', '..');
const out = process.argv[2]; fs.mkdirSync(out, { recursive: true });
let tiempos = null, t0 = 0, t1 = null;
if (process.argv[3] === '--tiempos') tiempos = process.argv[4].split(',').map(Number);
else { t0 = parseFloat(process.argv[3] || '0'); t1 = process.argv[4] ? parseFloat(process.argv[4]) : null; }
const THREE_DIR = path.dirname(path.dirname(require.resolve('three', { paths: [__dirname] })));
const tipos = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json' };
const srv = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  const f = u.startsWith('/three/') ? path.join(THREE_DIR, u.slice(7)) : path.join(__dirname, u);
  fs.readFile(f, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { 'Content-Type': tipos[path.extname(f)] || 'application/octet-stream' }); res.end(d); });
});
const du = (p, mime) => `data:${mime};base64,` + fs.readFileSync(p).toString('base64');
srv.listen(0, async () => {
  const port = srv.address().port;
  const b = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  pg.on('console', m => console.log('[pág]', m.text())); pg.on('pageerror', e => { console.error('ERROR', e); process.exit(1); });
  await pg.goto(`http://127.0.0.1:${port}/escena.html`);
  await pg.waitForFunction(() => typeof window.iniciar === 'function');
  const assets = {
    fuentes: { IDB: du('/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf', 'font/otf'), ISB: du('/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf', 'font/otf') },
    estampado: du(path.join(R, 'TRABAJO/v5/post/estampado.png'), 'image/png'),
  };
  const info = await pg.evaluate(a => window.iniciar(a), assets);
  fs.writeFileSync(path.join(out, 'eventos.json'), JSON.stringify(info, null, 1));
  const fps = 30, n = Math.round(info.TL.dur * fps);
  const lista = tiempos ? tiempos.map(t => Math.round(t * fps)) : Array.from({ length: (t1 ? Math.round(t1 * fps) : n) - Math.round(t0 * fps) }, (_, k) => Math.round(t0 * fps) + k);
  const ini = Date.now();
  for (const i of lista) {
    const png = await pg.evaluate(t => window.dibujar(t), i / fps);
    fs.writeFileSync(path.join(out, `${String(i + 1).padStart(4, '0')}.png`), Buffer.from(png.split(',')[1], 'base64'));
  }
  console.log(`cuadros: ${lista.length} en ${((Date.now() - ini) / 1000).toFixed(1)} s`);
  await b.close(); srv.close();
});
