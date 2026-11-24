// Roccé Life · V2: copia de scripts/life/render.js con fondo transparente (omitBackground) para las capas de la placa
// de cierre (PNG RGBA 1080×1920 que entran por video.master(overlays=…)).
// Uso: node life_v2_render.js trabajos.json   (lista de {html, out, w, h})
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  for (const j of jobs) {
    const page = await browser.newPage({ viewport: { width: j.w, height: j.h }, deviceScaleFactor: 1 });
    await page.goto('file://' + path.resolve(j.html));
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.resolve(j.out), clip: { x: 0, y: 0, width: j.w, height: j.h }, omitBackground: true });
    await page.close();
    console.log('ok', j.out);
  }
  await browser.close();
})();
