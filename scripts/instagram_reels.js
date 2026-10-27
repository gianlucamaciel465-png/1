const { chromium } = require('playwright');
const out = process.argv[2]; const urls = process.argv.slice(3);
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, locale: 'es-AR' });
  const p = await ctx.newPage();
  for (const [i, u] of urls.entries()) {
    try {
      const r = await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 30000 }); await p.waitForTimeout(6000);
      const info = await p.evaluate(() => ({ url: location.href, title: document.title, video: !!document.querySelector('video'),
        login: !!document.querySelector('input[name="password"]') || /accounts\/login/.test(location.href),
        og: (document.querySelector('meta[property="og:title"]') || {}).content || '' }));
      await p.screenshot({ path: `${out}/reel_${i + 1}.png` });
      console.log(JSON.stringify({ pedido: u, status: r && r.status(), ...info }));
    } catch (e) { console.log(u, 'ERROR', e.message.split('\n')[0]); }
  }
  await b.close();
})();
