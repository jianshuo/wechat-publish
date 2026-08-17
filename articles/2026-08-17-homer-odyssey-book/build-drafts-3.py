#!/usr/bin/env python3
"""Assemble three WeChat drafts (上/中/下) from book-styled converted chapters."""
import json, os, sys

DIR = os.path.dirname(os.path.abspath(__file__))
CH = os.path.join(DIR, "chapters-bookstyle")
THUMB = sys.argv[1]

pieces = {p['no']: p for p in json.load(open(f'{CH}/pieces.json'))}

DIGESTS = {
  'intro': '诺兰的《奥德赛》要上映了。可「奥德赛」到底是个人名、地名，还是件事？这本小书像听评书一样，把荷马三千年前的两个老故事讲明白。',
  '01': '「奥德赛」三个字说成人话：一个走了十年才回到家的人。打仗十年，回家路上又是十年——先把这个故事钉在心里。',
  '02': '荷马是谁？把他想象成三千年前古希腊顶顶有名的说书先生——他说的两个故事，成了整个西方文化的老祖宗。',
  '03': '没有纸笔的年代，几万行的史诗怎么一代代传下来？答案藏在说书人的套话、节拍和一场场篝火边的表演里。',
  '04': '一个「不和」的金苹果，三位女神争风吃醋，一场私奔——打了十年的特洛伊大战，就这么点着了。',
  '05': '十年围城打成拉锯战：希腊联军攻不进去，特洛伊守得住却出不来。两边的英雄，都在这十年里熬着。',
  '06': '《伊利亚特》整部史诗，讲的其实是一场赌气：第一勇士阿喀琉斯一怒罢战，战局天翻地覆。',
  '07': '城墙那一边的赫克托耳：明知打不过也要出城应战。特洛伊的顶梁柱，也是个好丈夫、好父亲。',
  '08': '打了十年打不下来的城，最后败给一只木马。史上最有名的一条计谋，和一场大战的落幕。',
  '09': '仗打赢了，回家的路却走了十年。《奥德赛》正式开场：奥德修斯的海上漂泊，从这里开始。',
  '10': '独眼巨人、塞壬女妖、把人变成猪的仙女——海上八十一难，跟孙悟空取经一个味道，一难一难闯过来。',
  '11': '他在海上漂了十年，家里也乱了十年：苦等的妻子佩涅罗佩，和一百多个赖在家里不走的求婚者。',
  '12': '乞丐模样回到家门口，没人认得他。一张只有主人拉得开的弓，认出了主人——然后是复仇。',
  '13': '古希腊的神会嫉妒、会偏心、会记仇，跟咱们的神仙不一样；人再英雄，也斗不过命。',
  '14': '为什么这两个老故事西方人念叨了三千年？就像《三国》《西游》之于咱们——它是西方文化的根。',
  '15': '功课做完了。带着这些门道走进影院，你看到的就不只是热闹，是门道。祝观影愉快。',
}

TITLE_OVERRIDE = {
  'intro': '回家的路走了十年（上）｜看诺兰《奥德赛》前，先听荷马说书',
  '06': '回家的路走了十年（中）｜第六章 · 阿喀琉斯的怒火：第一部史诗讲的就是一场赌气',
  '11': '回家的路走了十年（下）｜第十一章 · 家里的烂摊子：等他的妻子和一群赖着不走的人',
}

TAIL = ('<p><br></p>\n<section style="color:#7a7264;font-size:14px;">本篇选自小书'
        '《回家的路走了十年》——看诺兰《奥德赛》前的功课，全书共 15 章。'
        '点击「阅读原文」可在网页版阅读本章，还能收听朗读。</section>')

def article(no):
    p = pieces[no]
    content = open(f'{CH}/{no}.html').read() + '\n' + TAIL
    return {
        "title": TITLE_OVERRIDE.get(no, p['title']),
        "author": "王建硕",
        "digest": DIGESTS[no],
        "content": content,
        "thumb_media_id": THUMB,
        "content_source_url": p['source_url'],
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }

part1 = ['intro', '01', '02', '03', '04', '05']
part2 = ['06', '07', '08', '09', '10']
part3 = ['11', '12', '13', '14', '15']

for name, nos in (("draft-3a.json", part1), ("draft-3b.json", part2), ("draft-3c.json", part3)):
    d = {"articles": [article(n) for n in nos]}
    for a in d['articles']:
        assert len(a['digest']) <= 120, (name, a['title'], len(a['digest']))
        assert len(a['content']) < 20000, (name, a['title'], len(a['content']))
    json.dump(d, open(f'{DIR}/{name}', 'w'), ensure_ascii=False, indent=1)
    print(name, len(d['articles']), 'articles,',
          sum(len(a['content']) for a in d['articles']), 'total content chars')
