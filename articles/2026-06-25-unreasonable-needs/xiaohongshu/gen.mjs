import { writeFileSync, mkdirSync } from 'node:fs';

const OUT = process.argv[2] || '.';
mkdirSync(OUT, { recursive: true });

// ---- 卡片内容（按编辑逻辑拆分，不是机械按段）----
const BRAND = '王建硕 · 公众号';
const total = 8;

const cards = [
  {
    type: 'cover',
    kicker: '产品观察',
    title: '看似不合理的真实需求<br>才最值得做',
    sub: '一次被开发者说“不合理”的提需求经历',
  },
  {
    type: 'body',
    lead: '上周我给 VoiceDrop 的开发者 Cathy 提了几个需求。配音后改几个字、删掉一张照片、微调一下布局——我觉得再自然不过。',
    quote: '“你这 3 个需求，我听起来都挺……不（合理的）。”',
    foot: '我当时有点愣。这不就是最自然的使用流程吗？',
  },
  {
    type: 'quote',
    big: '技术做不到<br>和需求不合理<br>是两回事',
  },
  {
    type: 'body',
    head: '想想苹果',
    lead: 'iPhone 刚出来，很多人觉得触摸屏打字根本没法用。手机复制、电脑粘贴，AirDrop 一扔就过去——当年从工程角度看也都“很难搞”。',
    foot: '但苹果毫无感情地都做了出来。做出来之后，我们早就习以为常，想不起它曾经“不可能”。',
  },
  {
    type: 'body',
    head: '被“逼”出来的妙招',
    lead: 'Cathy 被我追问，只好认真想。她想出一个方案：给界面上每一行文字、每一张照片临时编个号——像水印一样。',
    quote: '“把第 18 行的‘我们’改成‘我’”“把第 3 号照片删掉”',
    foot: '语音识别就能精确落到具体位置。她说：“我特别得意。”',
  },
  {
    type: 'quote',
    big: '真实的需求<br>不会因为技术难就消失<br>它会一直等在那里',
  },
  {
    type: 'body',
    head: '两类需求',
    lead: '一类，是用户自己凑合出来的，做不到就不提，久了连自己都觉得不合理。',
    lead2: '另一类，是用户一直觉得“就应该这样”，提出来反而被说“没法干”。',
    foot: '第二类，才是真正值得做的东西——用户没有凑合，说明它真实存在，只是工程上还没好好面对。',
  },
  {
    type: 'end',
    big: '很多产品的进步<br>都从这里开始',
    sub: '有人坚持说“这是正常需求啊”，<br>然后另一个人，被逼着认真想了一下。',
    cta: '关注「王建硕」· 一起想清楚一点',
  },
];

// ---- 模板 ----
const baseCSS = `
*{margin:0;padding:0;box-sizing:border-box;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;}
html,body{width:1080px;height:1440px;}
.card{
  position:relative;width:1080px;height:1440px;overflow:hidden;
  background:#FAF7F0;
  font-family:"PingFang SC","Helvetica Neue",sans-serif;
  color:#23201B;
  padding:104px 96px 120px;
  display:flex;flex-direction:column;
}
.grain{position:absolute;inset:0;background:
  radial-gradient(1200px 600px at 85% -10%, rgba(192,73,47,.06), transparent 60%),
  radial-gradient(900px 700px at -10% 110%, rgba(192,73,47,.05), transparent 60%);
  pointer-events:none;}
.idx{position:absolute;top:104px;right:96px;font-size:30px;letter-spacing:2px;color:#B7AFA0;font-weight:600;}
.brand{position:absolute;left:96px;right:96px;bottom:84px;display:flex;align-items:center;justify-content:space-between;
  font-size:30px;color:#A59C8C;font-weight:500;letter-spacing:.5px;}
.brand .dot{width:14px;height:14px;border-radius:50%;background:#C0492F;margin-right:16px;display:inline-block;vertical-align:middle;}
.accent-rule{width:84px;height:8px;border-radius:8px;background:#C0492F;}
.em{color:#C0492F;}
.spacer{flex:1;}
</style>`;

function frame(inner, idx, brandRight = BRAND) {
  const isLast = idx === total;
  const more = idx && !isLast ? '右滑继续 →' : (isLast ? '完' : '');
  return `<!doctype html><html><head><meta charset="utf-8"><style>${baseCSS}
<body><div class="card"><div class="grain"></div>
${idx ? `<div class="idx">${String(idx).padStart(2,'0')} / ${String(total).padStart(2,'0')}</div>` : ''}
${inner}
<div class="brand"><span><span class="dot"></span>${brandRight}</span><span>${more}</span></div>
</div></body></html>`;
}

function render(card, i) {
  const idx = i + 1;
  if (card.type === 'cover') {
    return frame(`
      <div style="font-size:34px;letter-spacing:8px;color:#C0492F;font-weight:600;">${card.kicker}</div>
      <div class="accent-rule" style="margin:36px 0 0;"></div>
      <div class="spacer"></div>
      <div style="font-size:82px;line-height:1.34;font-weight:800;letter-spacing:1px;">${card.title}</div>
      <div style="margin-top:48px;font-size:40px;line-height:1.6;color:#6E665A;font-weight:400;">${card.sub}</div>
      <div class="spacer"></div>
    `, 0, BRAND);
  }
  if (card.type === 'quote' || card.type === 'end') {
    const sub = card.type === 'end'
      ? `<div style="margin-top:56px;font-size:42px;line-height:1.7;color:#6E665A;">${card.sub}</div>
         <div style="margin-top:72px;display:inline-block;font-size:38px;font-weight:700;color:#fff;background:#C0492F;padding:24px 44px;border-radius:18px;">${card.cta}</div>`
      : '';
    return frame(`
      <div style="font-size:200px;line-height:.7;color:#E5C9BF;font-weight:800;height:80px;">“</div>
      <div class="spacer"></div>
      <div style="font-size:86px;line-height:1.42;font-weight:800;letter-spacing:1px;">${card.big}</div>
      ${sub}
      <div class="spacer"></div>
    `, idx);
  }
  // body
  return frame(`
    ${card.head ? `<div style="font-size:38px;letter-spacing:4px;color:#C0492F;font-weight:700;">${card.head}</div><div class="accent-rule" style="margin:28px 0 8px;width:64px;height:7px;"></div>` : ''}
    <div class="spacer"></div>
    ${card.lead ? `<div style="font-size:52px;line-height:1.62;font-weight:600;">${card.lead}</div>` : ''}
    ${card.lead2 ? `<div style="font-size:52px;line-height:1.62;font-weight:600;margin-top:36px;">${card.lead2}</div>` : ''}
    ${card.quote ? `<div style="margin-top:48px;font-size:50px;line-height:1.55;font-weight:800;color:#C0492F;border-left:10px solid #E5C9BF;padding-left:36px;">${card.quote}</div>` : ''}
    ${card.foot ? `<div style="margin-top:48px;font-size:44px;line-height:1.66;color:#6E665A;font-weight:400;">${card.foot}</div>` : ''}
    <div class="spacer"></div>
  `, idx);
}

cards.forEach((c, i) => {
  const html = render(c, i);
  const name = `${String(i + 1).padStart(2, '0')}.html`;
  writeFileSync(`${OUT}/${name}`, html);
});
console.log(`wrote ${cards.length} html cards to ${OUT}`);
