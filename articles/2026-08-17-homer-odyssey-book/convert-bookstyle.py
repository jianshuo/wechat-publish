#!/usr/bin/env python3
"""Convert 书架 chapter HTML (homer-odyssey-for-moviegoers) → WeChat draft HTML,
keeping the book's ORIGINAL visual style (paper background, serif headings,
accent-blue strong/blockquote, panel boxes) as inline styles.

Differs from convert.py (plain house style with red bold): this one inlines
the source CSS so the WeChat article looks like the voicedrop book page.
"""
import re, json, sys, os

SRC = "/Users/jianshuo/.claude/jobs/c9e0b9fd/tmp/book"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chapters-bookstyle")
BASE = "https://jianshuo.dev/voicedrop/books/homer-odyssey-for-moviegoers"

# Original book CSS (see source pages' <style>) mapped to inline styles.
PAPER = 'background:#f7f2e7;padding:26px 18px;border-radius:10px;color:#33302a;line-height:1.85;'
SERIF = "font-family:'Noto Serif SC','Songti SC',serif;"
ACCENT = '#1F4E6B'
SOFT = '#7a7264'
PANEL = 'background:#fcf9f1;border:1px solid rgba(51,48,42,.14);border-radius:14px;padding:16px 20px;'
QUOTE = ('border-left:3px solid #1F4E6B;background:#fcf9f1;padding:12px 18px;'
         'margin:18px 0;border-radius:0 10px 10px 0;color:#7a7264;')

def inline(s):
    # strong → accent-blue semibold (original book style); dfn → plain bold
    s = re.sub(r'<strong>(.*?)</strong>', rf'<strong style="color:{ACCENT};font-weight:600;">\1</strong>', s, flags=re.S)
    s = re.sub(r'<dfn>(.*?)</dfn>', r'<strong>\1</strong>', s, flags=re.S)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def convert(inner):
    blocks = []
    pat = re.compile(r'<(p|h2|h3|ul|ol|blockquote)>(.*?)</\1>|<div class="plain">(.*?)</div>', re.S)
    for m in pat.finditer(inner):
        tag, body, plain = m.group(1), m.group(2), m.group(3)
        if plain is not None:
            ps = re.findall(r'<p>(.*?)</p>', plain, flags=re.S)
            innerhtml = ''.join(
                f'<p style="margin:0 0 8px;font-size:15px;color:{SOFT};">{inline(p)}</p>' if i < len(ps)-1
                else f'<p style="margin:0;font-size:15px;color:{SOFT};">{inline(p)}</p>'
                for i, p in enumerate(ps))
            blocks.append(f'<section style="{PANEL}">{innerhtml}</section>')
        elif tag == 'p':
            blocks.append(f'<p style="margin:14px 0;font-size:17px;">{inline(body)}</p>')
        elif tag == 'h2':
            blocks.append(f'<h2 style="{SERIF}font-size:23px;font-weight:600;margin:30px 0 12px;line-height:1.4;">{inline(body)}</h2>')
        elif tag == 'h3':
            blocks.append(f'<h3 style="{SERIF}font-size:18px;font-weight:600;margin:24px 0 8px;color:{ACCENT};">{inline(body)}</h3>')
        elif tag in ('ul', 'ol'):
            lis = re.findall(r'<li>(.*?)</li>', body, flags=re.S)
            # WeChat editor turns bare text nodes inside <ul> into empty <li> — join without newlines
            items = ''.join(f'<li style="margin:6px 0;font-size:16.5px;">{inline(li)}</li>' for li in lis)
            blocks.append(f'<{tag} style="margin:12px 0 12px 22px;padding:0;">{items}</{tag}>')
        elif tag == 'blockquote':
            blocks.append(f'<blockquote style="{QUOTE}"><p style="margin:0;">{inline(body)}</p></blockquote>')
    return '\n'.join(blocks)

os.makedirs(OUT, exist_ok=True)
pieces = []
files = ['intro'] + [f'{i:02d}' for i in range(1, 16)]
for f in files:
    h = open(f'{SRC}/{f}.html').read()
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', h, flags=re.S).group(1).strip()
    m = re.search(r'<article><article>(.*)</article>\s*</article>', h, flags=re.S) \
        or re.search(r'<article>(.*?)</article>', h, flags=re.S)
    content = f'<section style="{PAPER}">{convert(m.group(1))}</section>'
    leftovers = set(re.findall(r'<(\w+)[ >]', re.sub(
        r'</?(p|h2|h3|ul|ol|li|blockquote|section|strong|em|code|br)\b[^>]*>', '', content)))
    if leftovers:
        print(f'{f}: UNHANDLED TAGS {leftovers}', file=sys.stderr)
    open(f'{OUT}/{f}.html', 'w').write(content)
    pieces.append({'no': f, 'title': h1, 'source_url': f'{BASE}/{f}.html',
                   'chars': len(re.findall(r'[一-鿿]', re.sub(r'<[^>]+>', '', content)))})
json.dump(pieces, open(f'{OUT}/pieces.json', 'w'), ensure_ascii=False, indent=1)
for p in pieces:
    print(p['no'], p['chars'], p['title'])
