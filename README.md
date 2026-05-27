# wechat-publish workspace

写微信公众号文章用的工作目录。

## 怎么用

直接跟 Claude Code 说：

> 帮我写一篇公众号文章，思路是…

或者：

> /wechat-publish

把草稿粘进来。Claude 会调用 `wechat-publish` skill：
1. 轻润色（修错字、切段，保留你的语气）
2. 给 3 个标题候选
3. 生成 50–80 字摘要
4. 渲染题图（或用你提供的图）
5. 输出 `articles/YYYY-MM-DD-{slug}/` 目录，含 article.md / article.html / cover.png / meta.json
6. 给出 mp.weixin.qq.com 的发布步骤

## 文件结构

```
articles/
└── 2026-05-09-my-first-mac/
    ├── original.md     # 你最初给的草稿
    ├── article.md      # 润色后的源文件
    ├── article.html    # 粘贴到公众号编辑器用
    ├── cover.png       # 题图 (900x383)
    └── meta.json       # title, summary, author, date, slug
```

## 发布

文章包准备好后：

```bash
~/.claude/skills/wechat-publish/publish.sh articles/2026-MM-DD-slug
```

它会自动：
- 打开浏览器到 mp.weixin.qq.com
- 在 Finder 显示 cover.png
- 把正文 HTML 以 rich-text 格式放进剪贴板（Cmd+V 直接出排版）
- 终端弹出交互菜单：按 `1`/`2`/`3` 切换剪贴板为标题／作者／摘要

扫码登录后，编辑器正文 Cmd+V，再按数字切换、Cmd+V，封面拖进去，发布。

## skill 在哪儿

`~/.claude/skills/wechat-publish/`
- `SKILL.md` — 主流程
- `cover-template.html` — 题图模板，可改样式
- `render-cover.sh` — 题图渲染脚本
- `publish.sh` — Tier 1 发布助手

改题图的颜色／字体／版式：编辑 `cover-template.html` 顶部的 CSS 变量。
