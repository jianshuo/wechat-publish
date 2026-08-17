#!/usr/bin/env python3
"""Convert 书架 chapter HTML (homer-odyssey-for-moviegoers) → WeChat draft HTML.

Reuses the house conventions from upload-draft.sh's builder:
- red bold #ff0000 for <strong>, plain bold for <dfn>
- structural-only inline styles (h2/h3 size+bold, boxes, blockquote)
- <p><br></p> spacer between top-level blocks (editor-native paragraph gap)
"""
import re, json, html, sys, os

SRC = "/Users/jianshuo/.claude/jobs/c9e0b9fd/tmp/book"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chapters")
BASE = "https://jianshuo.dev/voicedrop/books/homer-odyssey-for-moviegoers"

RED = 'color:#ff0000;'
BOX = 'background:#f6f8fa;border-radius:6px;padding:14px 16px;'
QUOTE = 'border-left:3px solid #d9d9d9;padding:2px 14px;color:#666666;'

def inline(s):
    s = re.sub(r'<strong>(.*?)</strong>', rf'<strong style="{RED}">\1</strong>', s, flags=re.S)
    s = re.sub(r'<dfn>(.*?)</dfn>', r'<strong>\1</strong>', s, flags=re.S)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def convert(inner):
    blocks = []
    pos = 0
    pat = re.compile(r'<(p|h2|h3|ul|ol|blockquote)>(.*?)</\1>|<div class="plain">(.*?)</div>', re.S)
    for m in pat.finditer(inner):
        tag, body, plain = m.group(1), m.group(2), m.group(3)
        if plain is not None:
            ps = re.findall(r'<p>(.*?)</p>', plain, flags=re.S)
            innerhtml = ''.join(
                f'<p style="margin:0 0 10px;">{inline(p)}</p>' if i < len(ps)-1
                else f'<p style="margin:0;">{inline(p)}</p>'
                for i, p in enumerate(ps))
            blocks.append(f'<section style="{BOX}">{innerhtml}</section>')
        elif tag == 'p':
            blocks.append(f'<p>{inline(body)}</p>')
        elif tag == 'h2':
            blocks.append(f'<h2 style="font-size:1.4em;font-weight:bold;">{inline(body)}</h2>')
        elif tag == 'h3':
            blocks.append(f'<h3 style="font-size:1.2em;font-weight:bold;">{inline(body)}</h3>')
        elif tag in ('ul', 'ol'):
            lis = re.findall(r'<li>(.*?)</li>', body, flags=re.S)
            items = ''.join(f'<li>{inline(li)}</li>' for li in lis)
            blocks.append(f'<{tag}>{items}</{tag}>')
        elif tag == 'blockquote':
            blocks.append(f'<blockquote style="{QUOTE}"><p>{inline(body)}</p></blockquote>')
    return '\n<p><br></p>\n'.join(blocks)

os.makedirs(OUT, exist_ok=True)
pieces = []
files = ['intro'] + [f'{i:02d}' for i in range(1, 16)]
for f in files:
    h = open(f'{SRC}/{f}.html').read()
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', h, flags=re.S).group(1).strip()
    m = re.search(r'<article><article>(.*)</article>\s*</article>', h, flags=re.S) \
        or re.search(r'<article>(.*?)</article>', h, flags=re.S)
    content = convert(m.group(1))
    # leftover unknown tags check
    leftovers = set(re.findall(r'<(\w+)[ >]', re.sub(r'</?(p|h2|h3|ul|ol|li|blockquote|section|strong|em|code|br)\b[^>]*>', '', content)))
    if leftovers:
        print(f'{f}: UNHANDLED TAGS {leftovers}', file=sys.stderr)
    open(f'{OUT}/{f}.html', 'w').write(content)
    pieces.append({'no': f, 'title': h1, 'source_url': f'{BASE}/{f}.html',
                   'chars': len(re.findall(r'[一-鿿]', re.sub(r'<[^>]+>', '', content)))})
json.dump(pieces, open(f'{OUT}/pieces.json', 'w'), ensure_ascii=False, indent=1)
for p in pieces:
    print(p['no'], p['chars'], p['title'])
