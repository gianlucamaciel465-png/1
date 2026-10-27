const { chromium } = require('playwright');
const out = process.argv[2];
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, locale: 'es-AR',
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1' });
  console.log('cookies al iniciar:', (await ctx.cookies()).length);
  const page = await ctx.newPage();
  const visit = async (name, url) => {
    try {
      const r = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(5000);
      const info = await page.evaluate(() => ({
        title: document.title,
        login: !!document.querySelector('input[name="username"], input[name="password"]') || /accounts\/login/.test(location.href),
        reels: [...new Set([...document.querySelectorAll('a[href*="/reel/"], a[href*="/p/"]')].map(a => a.href.split('?')[0]))].slice(0, 12),
        texto: document.body.innerText.replace(/\s+/g, ' ').slice(0, 300),
        og: (document.querySelector('meta[property="og:description"]') || {}).content || ''
      }));
      await page.screenshot({ path: `${out}/${name}.png` });
      console.log(JSON.stringify({ name, status: r && r.status(), final: page.url(), ...info }));
    } catch (e) { console.log(name, 'ERROR', e.message.split('\n')[0]); }
  };
  await visit('feed', 'https://www.instagram.com/');
  await visit('perfil_rocce', 'https://www.instagram.com/rocce.ar/');
  await visit('perfil_rocce_reels', 'https://www.instagram.com/rocce.ar/reels/');
  console.log('cookies al final:', (await ctx.cookies()).map(c => c.name).join(','));
  await browser.close();
})();
