const path = require('path');
const { chromium } = require('/Users/jianshuo/.claude/skills/gstack/node_modules/playwright');

const DIR = __dirname;
const targets = [
  ['#xhs-01', 'xhs-01-cover.png'],
  ['#xhs-02', 'xhs-02-night.png'],
  ['#xhs-03', 'xhs-03-fairfield.png'],
  ['#xhs-04', 'xhs-04-yokan-street.png'],
  ['#xhs-05', 'xhs-05-bubble.png'],
  ['#xhs-06', 'xhs-06-mizu-yokan.png'],
  ['#xhs-07', 'xhs-07-closing.png'],
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1300, height: 1600 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(DIR, 'index.html'));
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(1200); // WebGL canvas settle
  for (const [sel, name] of targets) {
    const el = page.locator(sel);
    await el.scrollIntoViewIfNeeded();
    await page.waitForTimeout(150);
    await el.screenshot({ path: path.join(DIR, 'output', name) });
    console.log('rendered', name);
  }
  await browser.close();
})();
