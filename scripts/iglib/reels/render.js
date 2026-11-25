// Renderiza una pieza IGLIB cuadro a cuadro con Chromium (Playwright): canvas al doble (2160×3840) → JPEG q0,96 por
// cuadro; montar.sh lo baja a 1080×1920 con lanczos (zooms y textos de la hoja nítidos). Imágenes por file:// con
// --allow-file-access-from-files (el canvas no queda contaminado). Uso:
//   node render.js PIEZA(iglib1|iglib2) DATOS.json SALIDA_DIR [desde] [hasta] [paso] [escala]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [pieza, datos, out] = process.argv.slice(2, 5);
const desde = parseInt(process.argv[5] || '0'), hasta = process.argv[6] ? parseInt(process.argv[6]) : null;
const paso = parseInt(process.argv[7] || '1'), RS = parseFloat(process.argv[8] || '2');
fs.mkdirSync(out, { recursive: true });
(async () => {
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  pg.on('console', m => console.log('[pág]', m.text())); pg.on('pageerror', e => { console.error('ERROR', e); process.exit(1); });
  await pg.goto('file://' + path.join(__dirname, 'escena.html'));
  await pg.addScriptTag({ path: path.join(__dirname, pieza + '.js') });
  const D = JSON.parse(fs.readFileSync(datos, 'utf8'));
  const N = await pg.evaluate(async ({ D, RS }) => {
    const fuentes = [['Inter', 'Inter-Regular.otf', '400'], ['Inter', 'Inter-SemiBold.otf', '600'], ['Inter', 'Inter-Bold.otf', '700'],
      ['InterDisplay', 'InterDisplay-Bold.otf', '700'], ['InterDisplay', 'InterDisplay-SemiBold.otf', '600']];
    for (const [fam, f, w] of fuentes) { const ff = new FontFace(fam, `url(file:///usr/share/fonts/opentype/inter/${f})`, { weight: w }); await ff.load(); document.fonts.add(ff); }
    const c = document.getElementById('c'); c.width = 1080 * RS; c.height = 1920 * RS;
    window.CTX = c.getContext('2d'); window.CTX.imageSmoothingQuality = 'high';
    window.CACHE = {}; D.img = {}; window.DATOS = D; ESCENA.iniciar(D); return ESCENA.N;
  }, { D, RS });
  const fin = hasta === null ? N - 1 : hasta; const avisos = {}; let t0 = Date.now();
  for (let f = desde; f <= fin; f += paso) {
    const r = await pg.evaluate(async ({ f, RS }) => {
      const nec = ESCENA.necesita(f), D = window.DATOS;
      for (const [k, p] of Object.entries(nec)) {
        if (!window.CACHE[p]) { const im = new Image(); im.src = 'file://' + p; await im.decode(); window.CACHE[p] = im; }
        D.img[k] = window.CACHE[p];
      }
      const usadas = new Set(Object.values(nec)); for (const p of Object.keys(window.CACHE)) if (!usadas.has(p)) delete window.CACHE[p];
      const ctx = window.CTX; ctx.setTransform(RS, 0, 0, RS, 0, 0); ctx.clearRect(0, 0, 1080, 1920);
      const av = ESCENA.dibujar(ctx, f) || [];
      return { av, jpg: document.getElementById('c').toDataURL('image/jpeg', 0.96) };
    }, { f, RS });
    if (r.av.length) avisos[f] = [...new Set(r.av)];
    fs.writeFileSync(path.join(out, `${String(f).padStart(4, '0')}.jpg`), Buffer.from(r.jpg.split(',')[1], 'base64'));
    if (f % 50 === 0) console.log(`cuadro ${f} (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
  }
  fs.writeFileSync(path.join(out, 'avisos.json'), JSON.stringify(avisos, null, 1));
  console.log('listo', out, 'avisos en', Object.keys(avisos).length, 'cuadros');
  await b.close();
})();
