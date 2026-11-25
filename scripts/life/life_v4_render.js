// Roccé Life · V4 «¿Vuelve?» B · texto cinético cuadro a cuadro (Pedro, 25/11/2026).
// Carga UNA página (texto_v4.html, generada por life_v4.py etapa textos) y para cada cuadro n llama a window.frame(n),
// saca la captura 1080×1920 con fondo transparente (omitBackground, como life_v2_render.js) y guarda lo que quedó
// visible (window.visible(n): texto exacto por frase y renglón) para la evidencia.
// Uso: node life_v4_render.js trabajo.json   ({html, outdir, n0, n1, w, h, dump})
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const j = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: j.w, height: j.h }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(j.html));
  await page.evaluate(() => document.fonts.ready);
  const fuentes = await page.evaluate(async () => {
    await window.cargarFuentes();
    return Array.from(document.fonts).map(f => `${f.family} ${f.weight} ${f.status}`);
  });
  console.log('fuentes', JSON.stringify(fuentes));
  fs.mkdirSync(j.outdir, { recursive: true });
  const dump = {};
  for (let n = j.n0; n <= j.n1; n++) {
    await page.evaluate(n => window.frame(n), n);
    const out = path.join(j.outdir, `f_${String(n).padStart(4, '0')}.png`);
    await page.screenshot({ path: out, clip: { x: 0, y: 0, width: j.w, height: j.h }, omitBackground: true });
    dump[n] = await page.evaluate(n => window.visible(n), n);
    if (n % 50 === 0) console.log('cuadro', n);
  }
  fs.writeFileSync(j.dump, JSON.stringify({ fuentes, cuadros: dump }, null, 1));
  await browser.close();
  console.log('ok', j.n0, j.n1);
})();
