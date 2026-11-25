// IGLIB-3 · capas fijas de cada lámina con Chromium (Playwright), a 1080×1350 exactos:
//   base_LN.png        lámina completa sin video (las ventanas quedan con el fondo)
//   arriba_LN.png      lo que va POR ENCIMA del video (.arriba), fondo transparente
//   L6/arriba_KKK.png  L6 cuadro a cuadro (textos animados), fondo transparente
//   ventanas.json      posición y tamaño de cada ventana, medidos en la página
//   textos_medidos.json  texto, tamaño y fuente calculados de cada elemento con texto
// Uso: node capas.js PAGINA.html DIR_CAPAS CUADROS_L6
const { chromium } = require("/opt/node-tools/node_modules/playwright");
const path = require("path"), fs = require("fs");
(async () => {
  const [pagina, dir, nL6] = [process.argv[2], process.argv[3], parseInt(process.argv[4] || "132")];
  fs.mkdirSync(path.join(dir, "L6"), { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1400 }, deviceScaleFactor: 1 });
  await page.goto("file://" + pagina);
  await page.evaluate(() => document.fonts.ready);
  const fuentes = await page.evaluate(() => [...document.fonts].map(f => `${f.family} ${f.weight} ${f.status}`));
  console.log("fuentes:", fuentes.join(" | "));
  if (fuentes.some(f => !f.endsWith("loaded"))) throw new Error("hay fuentes sin cargar");
  const rotas = await page.evaluate(() => [...document.images].filter(i => !(i.complete && i.naturalWidth > 0)).map(i => i.getAttribute("src")));
  if (rotas.length) throw new Error("imágenes sin cargar: " + rotas.join(", "));
  const laminas = await page.$$("section.lamina");
  if (laminas.length !== 6) throw new Error(`hay ${laminas.length} láminas, se esperaban 6`);
  const ventanas = {};
  for (const l of laminas) {
    const id = await l.getAttribute("id");
    const caja = await l.boundingBox();
    const vs = await l.$$eval(".ventana", els => els.map(e => { const r = e.getBoundingClientRect(); return { id: e.dataset.v, x: r.x, y: r.y, w: r.width, h: r.height }; }));
    ventanas[id] = vs.map(v => ({ id: v.id, x: Math.round(v.x - caja.x), y: Math.round(v.y - caja.y), w: Math.round(v.w), h: Math.round(v.h) }));
    await l.screenshot({ path: path.join(dir, `base_${id}.png`) });
  }
  const tam = await page.evaluate(() => [...document.querySelectorAll("section.lamina *")]
    .filter(e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))
    .map(e => ({ lamina: e.closest("section").id, texto: e.textContent.trim().replace(/\s+/g, " "),
                 px: getComputedStyle(e).fontSize, fuente: getComputedStyle(e).fontFamily, peso: getComputedStyle(e).fontWeight })));
  fs.writeFileSync(path.join(dir, "textos_medidos.json"), JSON.stringify(tam, null, 1));
  await page.evaluate(() => document.body.classList.add("modo-arriba"));
  for (const l of laminas) {
    const id = await l.getAttribute("id");
    if (id === "L6") continue;
    await l.screenshot({ path: path.join(dir, `arriba_${id}.png`), omitBackground: true });
  }
  const l6 = laminas[5];
  for (let k = 0; k < nL6; k++) {
    await page.evaluate(k => estadoL6(k), k);
    await l6.screenshot({ path: path.join(dir, "L6", `arriba_${String(k).padStart(3, "0")}.png`), omitBackground: true });
  }
  fs.writeFileSync(path.join(dir, "ventanas.json"), JSON.stringify(ventanas, null, 1));
  console.log(JSON.stringify(ventanas));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
