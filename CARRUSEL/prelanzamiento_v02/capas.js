// Captura las capas fijas de cada lámina con Chromium (Playwright):
//   capas/base_NN.png   lámina completa (fondo, textos, fotos; en las ventanas, el primer cuadro del clip)
//   capas/arriba_NN.png lo que va POR ENCIMA del video (clase .arriba), con fondo transparente
//   capas/ventanas.json posición y tamaño exactos de cada ventana de video
// Uso: node capas.js
const { chromium } = require("playwright");
const path = require("path"), fs = require("fs");
(async () => {
  const dir = path.join(__dirname, "capas"); fs.mkdirSync(dir, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 1500 }, deviceScaleFactor: 1 });
  await page.goto("file://" + path.join(__dirname, "pagina.html"));
  await page.evaluate(() => document.fonts.ready);
  const fuentes = await page.evaluate(() => [...document.fonts].filter(f => f.status === "loaded").map(f => f.weight));
  console.log("fuentes cargadas:", fuentes.join(", "));
  const rotas = await page.evaluate(() => [...document.images].filter(i => !(i.complete && i.naturalWidth > 0)).map(i => i.getAttribute("src")));
  const placas = await page.$$("section.placa");
  if (placas.length !== 8) throw new Error(`hay ${placas.length} láminas, se esperaban 8`);
  const ventanas = {};
  for (let i = 0; i < placas.length; i++) {
    const n = String(i + 1).padStart(2, "0");
    const caja = await placas[i].boundingBox();
    const vs = await placas[i].$$eval(".ventana", (els) => els.map(e => { const r = e.getBoundingClientRect(); return { id: e.dataset.v, x: r.x, y: r.y, w: r.width, h: r.height }; }));
    ventanas[n] = vs.map(v => ({ id: v.id, x: Math.round(v.x - caja.x), y: Math.round(v.y - caja.y), w: Math.round(v.w), h: Math.round(v.h) }));
    await placas[i].screenshot({ path: path.join(dir, `base_${n}.png`) });
  }
  await page.evaluate(() => document.body.classList.add("modo-arriba"));
  for (let i = 0; i < placas.length; i++) {
    const n = String(i + 1).padStart(2, "0");
    await placas[i].screenshot({ path: path.join(dir, `arriba_${n}.png`), omitBackground: true });
  }
  fs.writeFileSync(path.join(dir, "ventanas.json"), JSON.stringify(ventanas, null, 1));
  console.log("imágenes sin cargar (pósters pendientes):", rotas.filter(s => !s.startsWith("capas/poster")).join(", ") || "ninguna");
  console.log(JSON.stringify(ventanas));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
