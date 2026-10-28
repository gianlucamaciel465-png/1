// Exporta cada placa de index.html como PNG de 1080 × 1350 px con Chromium (Playwright).
// Uso: node render.js SALIDA_DIR [VERSION]   → SALIDA_DIR/ROCCE_PRELAUNCH_01_vNN.png … _08_vNN.png
// Después: python3 finalizar.py SALIDA_DIR VERSION (perfil sRGB, controles y vista conjunta).
const { chromium } = require("playwright");
const path = require("path");
(async () => {
  const out = process.argv[2] || "salida"; const ver = process.argv[3] || "v01";
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 1500 }, deviceScaleFactor: 1 });
  await page.goto("file://" + path.join(__dirname, "index.html"));
  await page.evaluate(() => document.fonts.ready);
  const placas = await page.$$("section.placa");
  if (placas.length !== 8) throw new Error(`hay ${placas.length} placas, se esperaban 8`);
  // controles: fuentes cargadas e imágenes completas
  const fuentes = await page.evaluate(() => [...document.fonts].filter(f => f.status === "loaded").map(f => f.weight));
  const imgs = await page.evaluate(() => [...document.images].map(i => [i.getAttribute("src"), i.complete && i.naturalWidth > 0]));
  console.log("fuentes cargadas:", fuentes.join(", "));
  for (const [s, ok] of imgs) if (!ok) throw new Error("imagen sin cargar: " + s);
  for (let i = 0; i < placas.length; i++) {
    const f = path.join(out, `ROCCE_PRELAUNCH_${String(i + 1).padStart(2, "0")}_${ver}.png`);
    await placas[i].screenshot({ path: f });
    console.log(f);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
