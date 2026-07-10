#!/usr/bin/env python3
# Build 10 xiaohongshu card decks from the guizang seed templates.
import re, pathlib

ROOT = pathlib.Path(__file__).parent
SKILL = pathlib.Path.home() / '.claude/skills/guizang-social-card-skill/assets'
ED_SEED = (SKILL / 'template-editorial-card.html').read_text()
SW_SEED = (SKILL / 'template-swiss-card.html').read_text()

def splice(seed, posters, theme_attr, title):
    head = seed[:seed.rindex('<!-- POSTERS_HERE -->')]
    tail = seed[seed.rindex('</main>'):]
    html = head + '<!-- POSTERS_HERE -->\n' + posters + '\n  ' + tail
    html = re.sub(r'<html lang="zh-CN"[^>]*>', f'<html lang="zh-CN" {theme_attr}>', html)
    html = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', html)
    return html

def strip(name, i, n):
    return (f'<div class="issue-strip"><span>{name}</span><span>—</span>'
            f'<span>{i:02d} / {n:02d}</span></div>')

# ---------- Editorial page helpers (patterns proven in the nikko deck) ----------

def ed_cover(pid, kicker, title_html, title_size, img, obj_pos, cap, lead, sname, i, n, ratio='r-4x3'):
    return f'''
    <section class="poster xhs" id="{pid}">
      <canvas class="mag-bg" data-bg="ink-flow"></canvas>
      <div class="grain"></div>
      <div class="paper-wash"></div>
      <div class="content stack" style="gap:36px;">
        <p class="kicker" style="margin:0;">{kicker}</p>
        <h1 class="h-xl" style="font-size:{title_size}px; margin:0;">{title_html}</h1>
        <figure class="frame-img {ratio}">
          <img src="{img}" alt="" style="object-position:{obj_pos};">
        </figure>
        <p class="img-cap" style="margin-top:-16px;">{cap}</p>
        <p class="lead" style="font-size:30px; margin:0; flex:1;">{lead}</p>
      </div>
      {strip(sname, i, n)}
    </section>'''

def ed_quote(pid, corner, quote_html, qsize, body, source, sname, i, n):
    body_p = f'<p class="lead" style="font-size:30px; margin:28px 0 0;">{body}</p>' if body else ''
    return f'''
    <section class="poster xhs" id="{pid}">
      <canvas class="mag-bg" data-bg="ink-flow"></canvas>
      <div class="grain"></div>
      <p class="corner-tl" style="font-family:var(--mono); font-size:20px; letter-spacing:.22em; text-transform:uppercase; color:var(--muted);">{corner}</p>
      <div class="content stack" style="justify-content:center; gap:48px;">
        <div>
          <p class="pullquote" style="font-size:{qsize}px; line-height:1.36;">{quote_html}</p>
          {body_p}
        </div>
        <div>
          <hr class="rule-accent" style="margin:0 0 20px;">
          <p class="meta" style="margin:0;">{source}</p>
        </div>
      </div>
      {strip(sname, i, n)}
    </section>'''

def ed_field(pid, kicker, title_html, tsize, img, obj_pos, cap, body, sname, i, n, ratio='r-3x2', contain=False):
    fit = ' fit-contain' if contain else ''
    return f'''
    <section class="poster xhs" id="{pid}">
      <div class="grain"></div>
      <div class="paper-wash"></div>
      <div class="content stack" style="gap:36px;">
        <p class="kicker" style="margin:0;">{kicker}</p>
        <h2 class="h-xl" style="font-size:{tsize}px; margin:0;">{title_html}</h2>
        <figure class="frame-img {ratio}{fit}">
          <img src="{img}" alt="" style="object-position:{obj_pos};">
        </figure>
        <p class="img-cap" style="margin-top:-16px;">{cap}</p>
        <p class="lead" style="font-size:30px; margin:0; flex:1;">{body}</p>
      </div>
      {strip(sname, i, n)}
    </section>'''

def ed_essay(pid, kicker, title_html, pull_html, paras, callout, callout_src, sname, i, n):
    ps = '\n'.join(f'<p class="lead" style="font-size:31px; margin:0;">{p}</p>' for p in paras)
    co = (f'<div class="callout" style="font-size:33px;">{callout}'
          f'<span class="callout-src">{callout_src}</span></div>') if callout else ''
    return f'''
    <section class="poster xhs" id="{pid}">
      <canvas class="mag-bg" data-bg="ink-flow"></canvas>
      <div class="grain"></div>
      <div class="paper-wash"></div>
      <div class="content stack" style="gap:44px;">
        <p class="kicker" style="margin:0;">{kicker}</p>
        <h2 class="h-xl" style="margin:0;">{title_html}</h2>
        <div style="display:grid; grid-template-columns:5fr 7fr; gap:44px; flex:1;">
          <div style="border-right:1px solid var(--line); padding-right:44px;">
            <p class="pullquote" style="font-size:56px; line-height:1.36;">{pull_html}</p>
          </div>
          <div class="stack" style="gap:34px;">{ps}</div>
        </div>
        {co}
      </div>
      {strip(sname, i, n)}
    </section>'''

def ed_marginalia(pid, kicker, title_html, paras, margins, bottom, sname, i, n):
    ps = '\n'.join(f'<p class="lead" style="font-size:35px; line-height:1.7; margin:0;">{p}</p>' for p in paras)
    ms = '\n'.join(f'<p>{m}</p>' for m in margins)
    bt = (f'<div style="border-top:1px solid var(--line); padding-top:26px; font-family:var(--mono);'
          f' font-size:21px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted);">{bottom}</div>') if bottom else ''
    return f'''
    <section class="poster xhs" id="{pid}">
      <canvas class="mag-bg" data-bg="ink-flow"></canvas>
      <div class="grain"></div>
      <div class="paper-wash"></div>
      <div class="content stack" style="gap:40px;">
        <p class="kicker" style="margin:0;">{kicker}</p>
        <h2 class="h-xl" style="margin:0;">{title_html}</h2>
        <hr class="rule-accent" style="margin:0;">
        <div class="marginalia" style="flex:1;">
          <div class="stack" style="gap:48px;">{ps}</div>
          <div class="mg-col">{ms}</div>
        </div>
        {bt}
      </div>
      {strip(sname, i, n)}
    </section>'''

def ed_beforeafter(pid, kicker, title_html, tsize, b_kick, b_title, b_items, a_kick, a_title, a_items, note, sname, i, n):
    bl = '\n'.join(f'<li>{x}</li>' for x in b_items)
    al = '\n'.join(f'<li>{x}</li>' for x in a_items)
    nt = f'<p class="body" style="font-size:26px; margin:0; color:var(--muted);">{note}</p>' if note else ''
    return f'''
    <section class="poster xhs" id="{pid}">
      <canvas class="mag-bg" data-bg="ink-flow"></canvas>
      <div class="grain"></div>
      <div class="paper-wash"></div>
      <div class="content stack" style="gap:36px;">
        <p class="kicker" style="margin:0;">{kicker}</p>
        <h2 class="h-xl" style="font-size:{tsize}px; margin:0;">{title_html}</h2>
        <div class="beforeafter" style="flex:1; height:auto;">
          <div class="ba-block before" style="display:flex; flex-direction:column; justify-content:center;">
            <p class="kicker" style="margin:0 0 14px;">{b_kick}</p>
            <h3 class="h-md" style="font-size:44px; margin:0 0 18px;">{b_title}</h3>
            <ul class="body" style="margin:0; padding-left:1.2em; font-size:29px; line-height:1.9;">{bl}</ul>
          </div>
          <div class="ba-block" style="display:flex; flex-direction:column; justify-content:center;">
            <p class="kicker" style="margin:0 0 14px;">{a_kick}</p>
            <h3 class="h-md" style="font-size:44px; margin:0 0 18px;">{a_title}</h3>
            <ul class="body" style="margin:0; padding-left:1.2em; font-size:29px; line-height:1.9;">{al}</ul>
          </div>
        </div>
        {nt}
      </div>
      {strip(sname, i, n)}
    </section>'''

def ed_ledger(pid, kicker, title_html, tsize, rows, note, sname, i, n):
    # rows: [(nb, title, note)]
    rs = '\n'.join(
        f'''<div class="ledger-row" style="padding:36px 0;">
              <div class="ledger-nb">{nb}</div>
              <div class="ledger-title" style="font-size:44px;">{t}</div>
              <div class="ledger-note" style="font-size:24px; max-width:300px;">{nt}</div>
            </div>''' for nb, t, nt in rows)
    foot = f'<p class="lead" style="font-size:30px; margin:0;">{note}</p>' if note else ''
    return f'''
    <section class="poster xhs" id="{pid}">
      <canvas class="mag-bg" data-bg="ink-flow"></canvas>
      <div class="grain"></div>
      <div class="paper-wash"></div>
      <div class="content stack" style="gap:40px;">
        <p class="kicker" style="margin:0;">{kicker}</p>
        <h2 class="h-xl" style="font-size:{tsize}px; margin:0;">{title_html}</h2>
        <div class="ledger" style="flex:1; justify-content:center;">{rs}</div>
        {foot}
      </div>
      {strip(sname, i, n)}
    </section>'''

# ---------- Swiss page helpers ----------

def sw_meta_bottom(left, right):
    return (f'<hr class="hr-hairline"><div class="row" style="justify-content:space-between;">'
            f'<p class="t-meta">{left}</p><p class="t-meta">{right}</p></div>')

def sw_cover(pid, cat, date, title_html, lead, left, right, stats=None):
    st = ''
    if stats:
        cells = '\n'.join(
            f'<div><p class="num-xl" style="font-size:104px;">{n}</p>'
            f'<p class="t-meta" style="margin-top:14px;">{l}</p></div>' for n, l in stats)
        st = f'<div class="grid-3" style="border-top:1px solid var(--grey-2); padding-top:44px;">{cells}</div>'
    return f'''
    <section class="poster xhs" id="{pid}">
      <div class="content stack gap-8">
        <div class="chrome-min">
          <span class="t-cat">{cat}</span>
          <span class="t-meta">{date}</span>
        </div>
        <div class="stack gap-7">
          <h1 class="h-statement">{title_html}</h1>
        </div>
        <div class="grow"></div>
        {st}
        <hr class="hr-accent">
        <p class="lead" style="font-size:34px;">{lead}</p>
        {sw_meta_bottom(left, right)}
      </div>
    </section>'''

def sw_two(pid, cat, title_html, m1_kick, m1_title, m1_body, m2_kick, m2_title, m2_body, footer, left, right):
    return f'''
    <section class="poster xhs" id="{pid}">
      <div class="content stack gap-7">
        <p class="t-cat">{cat}</p>
        <h2 class="h-xl">{title_html}</h2>
        <div class="stack gap-6" style="flex:1; justify-content:center;">
          <div class="card-ink">
            <p class="t-cat">{m1_kick}</p>
            <h3 class="h-md" style="margin-top:16px; margin-bottom:8px;">{m1_title}</h3>
            <p class="lead" style="margin-top:22px;">{m1_body}</p>
          </div>
          <div class="card-outlined">
            <p class="t-cat">{m2_kick}</p>
            <h3 class="h-md" style="margin-top:16px; margin-bottom:8px;">{m2_title}</h3>
            <p class="lead" style="margin-top:22px;">{m2_body}</p>
          </div>
        </div>
        <p class="lead" style="font-size:32px;">{footer}</p>
        {sw_meta_bottom(left, right)}
      </div>
    </section>'''

def sw_rows(pid, cat, title_html, rows, footer, left, right):
    # rows: [(label, consequence)]
    rs = '\n'.join(
        f'''<div class="row" style="align-items:baseline; gap:40px; border-bottom:1px solid var(--grey-2); padding:34px 0;">
              <p class="t-meta" style="width:260px;">{lb}</p>
              <p class="h-md" style="font-size:48px;">{cq}</p>
            </div>''' for lb, cq in rows)
    return f'''
    <section class="poster xhs" id="{pid}">
      <div class="content stack gap-7">
        <p class="t-cat">{cat}</p>
        <h2 class="h-xl">{title_html}</h2>
        <div class="stack" style="flex:1; justify-content:center;">{rs}</div>
        <p class="lead" style="font-size:32px;">{footer}</p>
        {sw_meta_bottom(left, right)}
      </div>
    </section>'''

def sw_pipeline(pid, cat, title_html, steps, footer, left, right):
    # steps: [(nb, name, desc)]
    rs = '\n'.join(
        f'''<div class="card-outlined" style="display:grid; grid-template-columns:120px 1fr; gap:28px; align-items:baseline;">
              <p class="num-xl" style="font-size:88px; color:var(--accent);">{nb}</p>
              <div>
                <h3 class="h-md" style="font-size:50px;">{nm}</h3>
                <p class="lead" style="margin-top:22px;">{ds}</p>
              </div>
            </div>''' for nb, nm, ds in steps)
    return f'''
    <section class="poster xhs" id="{pid}">
      <div class="content stack gap-7">
        <p class="t-cat">{cat}</p>
        <h2 class="h-xl">{title_html}</h2>
        <div class="stack gap-6" style="flex:1; justify-content:center;">{rs}</div>
        <p class="lead" style="font-size:32px;">{footer}</p>
        {sw_meta_bottom(left, right)}
      </div>
    </section>'''

def sw_takeaway(pid, cat, title_html, body, quote, left, right):
    return f'''
    <section class="poster xhs" id="{pid}">
      <div class="content stack gap-8">
        <p class="t-cat">{cat}</p>
        <h2 class="h-statement" style="margin-top:24px;">{title_html}</h2>
        <div class="grow"></div>
        <div class="card-accent">
          <p class="lead" style="font-size:34px; line-height:1.6;">{quote}</p>
        </div>
        <p class="lead" style="font-size:32px;">{body}</p>
        {sw_meta_bottom(left, right)}
      </div>
    </section>'''

# ================= DECK DEFINITIONS =================
decks = {}

# ---- 01 肉丸 (Editorial Kraft, 3p) ----
S = '在 IKEA 餐厅点了一份瑞典肉丸'
decks['01-ikea-meatballs'] = ('kraft-paper', S, [
    ed_cover('xhs-01', '晚饭 · IKEA 船桥', '去 IKEA 吃肉丸，<br>端上来的是三文鱼', 72,
             'assets/tray.jpg', 'center 55%', '烟熏三文鱼 · 芒果杏仁豆腐',
             '本来是冲着瑞典小肉丸来的。站在取餐台前，灯箱菜单一格一格排开。', S, 1, 3),
    ed_field('xhs-02', 'Menu · 灯箱菜单', '全是日文标价', 76,
             'assets/menu.jpg', 'center 50%', '瑞典肉丸 ¥1,290 · 植物肉丸 ¥990',
             '瑞典肉丸 12 个，1290 日元；植物肉丸 12 个，990 日元；旁边还有夏季限定的三文鱼、鱼薯条，一格挨一格。',
             S, 2, 3, ratio='r-4x3', contain=True),
    ed_quote('xhs-03', 'The Verdict · 结账之后', '「说好的<br>肉丸呢。」', 84,
             '端上托盘的：一盘撒满莳萝碎的烟熏三文鱼，一小碗芒果杏仁豆腐。',
             '「在 IKEA 餐厅点了一份瑞典肉丸」 — 王建硕', S, 3, 3),
])

# ---- 02 摆法 (Editorial Kraft, 4p) ----
S = '在宜家看家具的这套摆法'
decks['02-ikea-display'] = ('kraft-paper', S, [
    ed_cover('xhs-01', '零售观察 · IKEA', '宜家这套摆法，<br>就一个字：快', 76,
             'assets/workspace.jpg', 'center 40%', 'デスク・チェア · Desks & Chairs',
             '不是海报，不是效果图，是那张桌子、那把椅子摆在那儿，你走过去就是。', S, 1, 4),
    ed_field('xhs-02', '样板 · ¥13,000', '一整套工作区，<br>替你摆好了', 70,
             'assets/desk13000.jpg', 'center 45%', 'このワークスペース全部で ¥13,000',
             '红柱子上贴着牌子：这一套工作区加起来一万三千日元。白桌子上架着升降台，笔记本摆好，站着也能用。',
             S, 2, 4, ratio='r-4x3'),
    ed_field('xhs-03', '椅子 · 一字排开', '你要挑，<br>一眼就挑得出来', 70,
             'assets/chairs.jpg', 'center 50%', '黄的白的粉的蓝的 · 坐垫单卖',
             '各种转椅一字排开，地上还叠着一摞黑网椅。往里走还有几把休闲椅随手搁在过道边上。',
             S, 3, 4, ratio='r-3x2'),
    ed_quote('xhs-04', 'Retail Note · 看完的感受', '「你不用想象，<br>它已经替你<br>摆好了。」', 76,
             '', '「在宜家看家具的这套摆法」 — 王建硕', S, 4, 4),
])

# ---- 03 桌子 (Editorial Kraft, 3p) ----
S = '在 IKEA 逛桌子'
decks['03-ikea-tables'] = ('kraft-paper', S, [
    ed_cover('xhs-01', 'Field Note · 随手拍', '同样是两人小方桌，<br>价格差出一倍多', 68,
             'assets/pintorp.jpg', 'center 45%', 'PINTORP · ¥9,990',
             '三张照片，一边走一边随手拍的。白腿橡木面的这张，一个人吃饭刚刚好。', S, 1, 3),
    ed_field('xhs-02', '对比 · 两张方桌', '9,990 对 22,990', 76,
             'assets/table22990.jpg', 'center 50%', '浅木色圆腿 · 配宝蓝色圆坐垫的木椅',
             '往前走几步又一张方桌，桌上摆着小木盒和说明卡。同样是两人份的小方桌，价格差出一倍多。',
             S, 2, 3, ratio='r-4x3'),
    ed_field('xhs-03', '收尾 · 厨房用品区', '最后拿起来的，<br>是个 2,499 的小东西', 64,
             'assets/nalblecka.jpg', 'center 50%', 'NALBLECKA · 金属加竹 · Lukas Bazle',
             '38×13×28 厘米，放调味料的两层小架子。没了，就逛到这儿。',
             S, 3, 3, ratio='r-4x3'),
])

# ---- 04 池子 (Editorial Indigo, 4p) ----
S = '游泳只需要一个池子'
decks['04-pool-only'] = ('indigo-porcelain', S, [
    ed_cover('xhs-01', '游泳 · 傍晚', '游泳只需要<br>一个池子', 84,
             'assets/pool1.jpg', 'center 40%', '东京奥林匹克水上运动中心',
             '想清楚自己到底要什么，其实挺重要的。', S, 1, 4),
    ed_marginalia('xhs-02', '游完之后', '游完了，<br>人却空落落的', [
        '今天去奥林匹克体育中心游泳。游完了，却有一种说不上来的虚无感，好像这一趟没什么意义。',
        '本来旁边那个月岛中心就挺好的。',
        '在游泳这件事上，有一个池子、你能在里面游，这大概就是你的全部需求了。'],
        ['奥体中心 ↓', '50 米标准池', '观众席', '', '月岛中心 ↓', '一池水'],
        '', S, 2, 4),
    ed_beforeafter('xhs-03', '对比 · 两个泳池', '好处一大堆，<br>用得上的只有水', 72,
        '奥体中心 · 好处一大堆', 'Building 好看，设施国际化',
        ['两边有观众席', '50 米的标准池', '跟你的游泳，一点关系没有'],
        '月岛中心 · 全部需求', '一个池子，能游',
        ['就在旁边', '这就够了'],
        '这些表面上的好处，我却为它花了那么多时间。', S, 3, 4),
    ed_quote('xhs-04', '想了半天', '「不能为了表面上的东西，<br>放弃真正要的<br>那件事。」', 68,
             '', '「游泳只需要一个池子」 — 王建硕', S, 4, 4),
])

# ---- 05 不划算 (Swiss IKB, 4p) ----
decks['05-not-worth-it'] = ('swiss:ikb', '去奥林匹克中心游泳，不划算', [
    sw_cover('xhs-01', 'Swim · 算账', '2026.07.10',
             '去奥体游泳，<br>不划算。',
             '游完泳，得出一个结论。最不值的，是时间。',
             'Tokyo Aquatics Centre', '王建硕',
             stats=[('3 站', '电车 · 三站路'), ('20 分', '下车还要走'), ('×2', '原路再来一遍')]),
    sw_two('xhs-02', 'Same Time · 同一段时间', '一个已经收工，<br>一个还没下水',
           '月岛中心', '泳游完，人到家', '就在家旁边。同一段时间里，这边已经收工了。',
           '奥体中心', '才刚走到池子边', '走到车站，坐三站，下来再走十六到二十分钟。',
           '游完，还要原路再来一遍。', 'Timing · 对照', '05 · Swim'),
    sw_rows('xhs-03', 'Checklist · 听着挺好', '设施一大堆，<br>一样都用不上',
            [('看台', '整齐，但用不上'), ('泳道', '很长，也用不上'), ('人少', '听着好，还是用不上')],
            '你在乎的是那个池子，就是那一池水。', 'Facilities · 盘点', '王建硕'),
    sw_takeaway('xhs-04', 'Verdict · 结论', '下次，<br>在近处游。',
                '省下来这段路，我干什么都好。',
                '这时间是没必要花的。', '「去奥林匹克中心游泳这事，实在不划算」', '2026.07'),
])

# ---- 06 新木场 (Editorial Forest Ink, 4p) ----
S = '从新木场站走到水上运动中心'
decks['06-shinkiba-walk'] = ('forest-ink', S, [
    ed_cover('xhs-01', 'Citywalk · 新木场', '走去 2020 奥运的<br>游泳主场', 74,
             'assets/hall.jpg', 'center 50%', '木质弧顶大厅 · 几个小孩在地上跑',
             '这条路走得有点远，但不算白走。', S, 1, 4),
    ed_ledger('xhs-02', 'Route · 两条路', '结论先摆着：<br>以后不走这条', 72,
              [('A', '潮见站 · 1.0 km', '16 分钟，以前一直走这边'),
               ('B', '新木场站 · 1.6 km', '24 分钟，这次试的新路'),
               ('→', '差出 8 分钟', '换路本来就是想试试不同的线')],
              '', S, 2, 4),
    ed_field('xhs-03', '路上 · Park Path', '一路全是公园，<br>这在东京挺少见', 66,
             'assets/park.jpg', 'center 50%', '风不错 · 有点晒 · 草被吹得嗡嗡响',
             '有割草机的声音，有车流声，可它到底还是一条很安静的路。',
             S, 3, 4, ratio='r-3x2'),
    ed_field('xhs-04', '到了 · Aquatics Centre', '在奥运原样的池子里，<br>有一种仪式感', 60,
             'assets/venue.jpg', 'center 45%', '顶上大，下面小，四边像屋檐一样往外展开',
             '50 米标准池，全场一样深，两边是长长的观众台，水质清澈。你可以想象观众台上坐满人的样子。',
             S, 4, 4, ratio='r-4x3'),
])

# ---- 07 停开发 (Swiss IKB, 4p) ----
decks['07-vd-pause'] = ('swiss:ikb', 'VoiceDrop 的开发，到这儿先停一下', [
    sw_cover('xhs-01', 'Product · VoiceDrop', '2026.07.10',
             '开发到这儿，<br>先停一下。',
             '不是因为它完美——是该有的都有了。接下来做市场和运营。',
             'VoiceDrop · 口述', '王建硕',
             stats=[('01', '记录'), ('02', '挖文'), ('03', '成文')]),
    sw_pipeline('xhs-02', 'Core Loop · 最核心的一条线', '记录，挖文，<br>用你的风格写',
                [('01', '记录', '你对着它说一通，想到哪说到哪。'),
                 ('02', '挖文', '它把有用的话挖出来。'),
                 ('03', '成文', '照着你的口气，写成文章。')],
                '这是一件事，不是三件事。', 'Voice → Article', '07 · VD'),
    sw_two('xhs-03', 'Also Shipped · 另外两块', '文章有了图，<br>才像个作品',
           '图片', '预览图 + 解释图', '公众号的那张预览图，还有文章里的解释图。不然就是一堆字。',
           '采访', '它会追着你问', '你没说透的地方，它替读者盯着。',
           '还有很多，就不一一数了。', 'Features · 盘点', '王建硕'),
    sw_takeaway('xhs-04', 'Next · 下一个阶段', '市场，<br>和运营。',
                '再往下堆功能，堆的多半是我自己的手痒，不是产品真需要。',
                '做的时候总觉得下一个功能才是关键。真到要停的时候才发现，最核心的那三样，早就在那儿了。',
                '「VoiceDrop 的开发，到这儿我先停一下」', '2026.07'),
])

# ---- 08 Excel (Editorial Ink Classic, 5p) ----
S = '两个人能不能做出一个 Excel'
decks['08-two-people-excel'] = ('ink-classic', S, [
    # M09 atmospheric cover
    f'''
    <section class="poster xhs" id="xhs-01">
      <canvas class="mag-bg" data-bg="ink-flow"></canvas>
      <div class="grain"></div>
      <div class="content stack" style="justify-content:center; gap:44px;">
        <p class="kicker" style="margin:0;">半夜聊出来的 · Late Night</p>
        <h1 class="h-display" style="font-size:104px; margin:0;">两个人，能不能<br>做出一个 Excel</h1>
        <p class="h-sub" style="margin:0;">A dead-knot question, untangled.</p>
        <p class="lead" style="font-size:30px; margin:0;">半夜跟人聊我们那个 APP 到底该怎么做，聊着聊着，聊到一个死结上。</p>
      </div>
      {strip(S, 1, 5)}
    </section>''',
    ed_quote('xhs-02', 'The Knot · 死结', '「要么不做，<br>要么完整地做。<br>做一半，没人能用。」', 64,
             '聊天、文档、日历、邮箱——少一块都是残的，人家不会为了一个残品换掉现在用的东西。',
             '深夜聊天记录 · 第一句', S, 2, 5),
    ed_ledger('xhs-03', 'Headcount · 人数', '做一个 Excel，<br>要多少人', 76,
              [('01', '微软 · 一千多人', '当年做 Excel 用的人数'),
               ('02', '飞书 · 接近一千人', '现在做表格也是这个量级'),
               ('03', '我们 · 两个人', '——')],
              '它的厉害是海量功能、海量细节一点点堆出来的。你没有那么多人，就堆不出那么多东西。',
              S, 3, 5),
    ed_essay('xhs-04', 'The Bet · 凭什么', '那凭什么<br>是我们俩', '我们有<br>cloud，<br>他们没有。',
             ['想把完整的 Excel 做出来，跟现在从头做一个浏览器一样，基本不可能了。全世界都不太可能再有人干这事。',
              '去钻研别人为什么做得差，没有意义。我们只用做得好就行了。',
              '而且——你正常办公，本来也用不到 Excel 那么多功能。'],
             '', '', S, 4, 5),
    ed_quote('xhs-05', '松一口气的那句话', '「我们不做 Excel，<br>我们对标 Notion<br>的数据库。」', 62,
             '我们是数据库，不是表格。这么一想，这个东西是有可能做出来的。',
             '「两个人能不能做出一个 Excel」 — 王建硕', S, 5, 5),
])

# ---- 09 和牛 (Editorial Midnight Ink, 3p) ----
S = '在家煎和牛'
decks['09-wagyu'] = ('midnight-ink', S, [
    ed_cover('xhs-01', '晚饭 · 战报', '在家煎和牛，<br>跟打仗一样', 80,
             'assets/wagyu.jpg', 'center 60%', '一片片带着焦褐色的边 · 一小碗蘸料',
             '锅一热，油唰唰唰地往外蹦，人在灶台前躲都没处躲。', S, 1, 3),
    ed_marginalia('xhs-02', '经验 · 虾脯 vs 和牛', '虾脯好办，<br>和牛不是', [
        '以前煎的都是虾脯。虾脯好办：扔进去，翻个面，出锅。',
        '这回换成和牛，才知道不是一回事。最后厨房里到处都是油点子。',
        '盘子里摆出来倒是像那么回事。可代价是整个灶台的战场。'],
        ['虾脯 ↓', '翻面，出锅', '', '和牛 ↓', '油点子', '灶台战场'],
        '', S, 2, 3),
    ed_quote('xhs-03', 'The Verdict · 收拾完灶台', '「以后<br>再也不煎了。」', 92,
             '', '「在家煎和牛，跟打仗一样」 — 王建硕', S, 3, 3),
])

# ---- 10 原型 (Editorial Ink Classic, 4p) ----
S = '最早那个原型，脑子里装着一个人'
decks['10-one-real-person'] = ('ink-classic', S, [
    f'''
    <section class="poster xhs" id="xhs-01">
      <canvas class="mag-bg" data-bg="ink-flow"></canvas>
      <div class="grain"></div>
      <div class="content stack" style="justify-content:center; gap:44px;">
        <p class="kicker" style="margin:0;">Product Note · 原型期</p>
        <h1 class="h-display" style="font-size:108px; margin:0;">脑子里装着<br>一个具体的人</h1>
        <p class="h-sub" style="margin:0;">Not a persona. A person.</p>
        <p class="lead" style="font-size:30px; margin:0;">做最早那版产品原型的时候，我脑子里装着一个真人，不是一张用户画像。</p>
      </div>
      {strip(S, 1, 4)}
    </section>''',
    ed_beforeafter('xhs-02', 'Persona vs Person', '画像填得出来，<br>人才记得住', 72,
        '一张画像 · Persona', '年龄、职业、月收入', ['每天刷几小时手机', '一张表填出来的', '我从来记不住，也不信'],
        '一个真人 · Person', '每个取舍都问他', ['这个东西，他会不会用？', '会不会嫌烦？', '会不会觉得写出来的不像他自己？'],
        '', S, 2, 4),
    ed_essay('xhs-03', 'The Filter · 两条', '两条得<br>同时成立', '又想写，<br>又肯让机器<br>搭把手。',
             ['喜欢写公众号，同时又愿意接受用 AI 来帮着写文章。',
              '光爱写、抵触 AI 的人不算；愿意用 AI、可自己压根没有要写的冲动的人，也不算。',
              '得是卡在这个交叉点上的人。'],
             '', '', S, 3, 4),
    ed_quote('xhs-04', '所以', '「有一个活人在那儿，<br>比一张画像<br>顶用多了。」', 66,
             '这样的人，倒是可以拉来试一试。',
             '「最早那个原型，脑子里装着一个人」 — 王建硕', S, 4, 4),
])

# ================= BUILD =================
for slug, (theme, title, pages) in decks.items():
    posters = '\n'.join(pages)
    if theme.startswith('swiss:'):
        html = splice(SW_SEED, posters, f'data-accent="{theme.split(":")[1]}"', title + ' · Social Cards')
    else:
        html = splice(ED_SEED, posters, f'data-theme="{theme}"', title + ' · Social Cards')
    out = ROOT / slug / 'index.html'
    out.write_text(html)
    print(f'built {slug}: {len(pages)} pages')
