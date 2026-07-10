const path = require('path');
const fs = require('fs');
const { chromium } = require('/Users/jianshuo/.claude/skills/gstack/node_modules/playwright');

const ROOT = __dirname;
const decks = fs.readdirSync(ROOT).filter(d => fs.existsSync(path.join(ROOT, d, 'index.html')));

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1300, height: 1600 }, deviceScaleFactor: 1 });
  for (const deck of decks) {
    await page.goto('file://' + path.join(ROOT, deck, 'index.html'));
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(1000);
    const ids = await page.$$eval('section.poster', els => els.map(e => e.id));
    for (const id of ids) {
      const el = page.locator('#' + id);
      await el.scrollIntoViewIfNeeded();
      await page.waitForTimeout(120);
      await el.screenshot({ path: path.join(ROOT, deck, 'output', id + '.png') });
    }
    console.log('rendered', deck, ids.length, 'pages');
  }
  await browser.close();
})();
