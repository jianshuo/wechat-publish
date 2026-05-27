# wjs-syndicating-articles — Design Spec

**Date:** 2026-05-23
**Author:** 王建硕 (with Claude)
**Status:** Approved design, ready for implementation plan

## Goal

每天定时,把最新发布的一篇公众号文章(`articles/YYYY-MM-DD-slug/`)自动扇出(syndicate)到多个社交平台。

设计的第一优先级是 **稳定 + 简单**。用户的明确取舍:**"能手工但稳定" 胜过 "全自动但脆弱"**。因此凡是没有干净 API 的平台,一律走"自动备料 + 手动点发布",绝不靠脆弱的浏览器登录态去硬发。

## Locked Decisions（来自 brainstorming）

1. **混合自动化**:有干净 API 的平台真发;没 API 的平台由 skill 把适配好的文案+配图备进"待发件箱(outbox)",自动打开能开的网页编辑器,用户只剩"粘贴 + 点发布"。
2. **一套文案走天下**:从文章抽一份核心文案,各平台只做长度截断/链接放置,不做逐平台重写。
3. **全自动不打断**:API 平台直接发出、不问;无 API 平台自动备料 + 推送通知,也不问。
4. **每天定时触发**(`/schedule` daily),挑最新一篇还没分发过的文章。

## Platforms & Modes

| 平台 | 模式 | 认证 | 缺/过期凭证时 |
|---|---|---|---|
| **X** | API 全自动 | `xurl`(已就绪) | — |
| **Bluesky** | API 全自动 | handle + app password（`com.atproto`） | 降级为 outbox（手动） |
| **Threads** | API 全自动 | Meta 长效 access token + user id | 降级为 outbox（手动） |
| **LinkedIn** | API 全自动 | 个人 access token + author URN（`/v2/ugcPosts`） | 降级为 outbox（手动） |
| **Facebook** | outbox + 顺手开 web | — | — |
| **小红书** | outbox（图存好 + 文案进剪贴板，AirDrop 到手机发） | — | — |
| **即刻 (Jike)** | outbox + 顺手开 web | — | — |
| **知乎 (Zhihu)** | outbox + 顺手开 web（走「想法」短文案；长文搬运为未来可选） | — | — |

**为什么小红书/即刻只能手动**:两者以手机 App 为主,web 端发图能力很弱或不存在,且无公开发布 API。强行浏览器自动化会经常断,违背"稳定"目标。

**核心稳定原则**:
- 每个平台是一个**独立的 try/catch 步骤**;任一平台失败/超时,绝不影响其它平台。
- **凭证缺失或过期 → 自动降级为 outbox(手动)**,绝不让整次 run 整体报错。
- **幂等**:`state/history.jsonl` 按 `(slug, platform)` 去重;重复跑只补发还没成功的 (文章×平台) 组合,永不重复发。

## One Copy 的抽取规则

从 `article.md` + `meta.json` 抽出**一份核心文案**:
- 一段最 quotable 的核心句/小段,**≤120 字**(保证能塞进 X 的 280 字符上限;中文每字算 2)。
- 一行软性 CTA/链接(指向公众号文章；默认署名/订阅目标为「**王建硕**」)。
- 保留王建硕语气:平实、家常比喻、不写营销腔;**不**加 hashtag、不加 @、不堆 emoji（除非原文有）。

各平台仅做放置/截断:

| 平台 | 长度上限 | 链接处理 | 图片 |
|---|---|---|---|
| X | 280 字符 | 正文塞得下就附,否则放 reply | 可选 cover |
| Bluesky | 300 graphemes | 正文内联 | 可选 |
| Threads | 500 字符 | 正文内联 | 可选 |
| LinkedIn | 同核心文案 + 链接 | 正文内联 | 可选 |
| Facebook / 即刻 | 同核心文案 + 链接 | 正文内联 | 可选 |
| 小红书 | 同核心文案 | 文案进剪贴板 | **主图必带**(cover.png / illustration.png) |

小红书的主图来源:优先 `cover.png`,无则 `illustration.png`,再无则跳过图片并在 OPEN.md 标注。

## Slug 约定（canonical key）

`slug` = 文章 folder 的 basename(带日期前缀,如 `2026-05-15-less-chat-more-program`)。`history.jsonl`、outbox 目录名、与 tweeting skill 的 X 去重,全用这个统一 key。**不要用 `meta.json` 里的干净 slug** —— 那会和脚本用的 basename 对不上,导致 `fully-done` 永远判不出 true、文章被反复重选。

为杜绝 LLM 临时拼 key 造成的漂移,扇出逻辑收进确定性脚本 `syndicate.sh`(见下),`slug` 一律由脚本 `basename "$FOLDER"` 计算,SKILL.md 的编排不再手写 slug 或平台循环。

## 选文章策略：只看最新一篇

`pick-next-article.sh` 只看**最新一篇**(folder 名按日期倒序的第一个)。若它已全部分发完 → 输出空 = rest day,**不往回翻更老的文章**。这样定时跑只会处理"以后新发的文章",不会把历史存档倒着全发一遍。

## Directory & State

```
~/.claude/skills/wjs-syndicating-articles/
├── SKILL.md
├── config.json              # 启用哪些平台、各自模式(api/outbox)、定时点、文章源路径
├── secrets.json             # gitignore：bluesky / threads / linkedin 凭证
├── .gitignore               # 屏蔽 secrets.json 和 state/、outbox/
├── scripts/
│   ├── pick-next-article.sh # 最新一篇还没分发完的文章 folder（按日期倒序，跳过 history 里已全发完的）
│   ├── post-x.sh            # xurl POST /2/tweets
│   ├── post-bluesky.sh      # 创建 session → com.atproto.repo.createRecord
│   ├── post-threads.sh      # Threads API：创建 media container → publish
│   ├── post-linkedin.sh     # /v2/ugcPosts
│   └── build-outbox.sh      # 给手动平台备料：post.txt + image.png + OPEN.md
├── outbox/<date>-<slug>/    # post.txt（核心文案）+ image.png（主图）+ OPEN.md（每平台粘贴指引+链接）
└── state/
    └── history.jsonl        # 每 (slug, platform) 一行 JSON record
```

`config.json` 字段（示意）:

```json
{
  "articles_dir": "/Users/jianshuo/code/wechat-publish/articles",
  "author": "王建硕",
  "schedule": "10:00",
  "platforms": {
    "x":        { "mode": "api" },
    "bluesky":  { "mode": "api" },
    "threads":  { "mode": "api" },
    "linkedin": { "mode": "api" },
    "facebook": { "mode": "outbox", "web_compose": "https://www.facebook.com/" },
    "xiaohongshu": { "mode": "outbox" },
    "jike":     { "mode": "outbox", "web_compose": "https://web.okjike.com/" },
    "zhihu":    { "mode": "outbox", "web_compose": "https://zhuanlan.zhihu.com/write" }
  }
}
```

`secrets.json`（gitignore，缺字段即降级）:

```json
{
  "bluesky":  { "handle": "...", "app_password": "..." },
  "threads":  { "access_token": "...", "user_id": "..." },
  "linkedin": { "access_token": "...", "author_urn": "urn:li:person:..." }
}
```

`history.jsonl` 每行:

```json
{"date":"2026-05-23","slug":"2026-05-15-less-chat-more-program","platform":"x","status":"posted","url":"https://x.com/jianshuo/status/...","post_id":"..."}
```

`status` ∈ `posted`(API 真发成功) / `queued`(已备进 outbox 待手动发;API 平台缺凭证降级时也记 `queued` 并带 `reason:"no_creds"`) / `failed`(尝试失败,下次重试) / `skipped`(已在别处发过,如 tweeting skill 已发 X)。

"已完成、本次不再重试"的判定 = status ∈ {`posted`, `queued`, `skipped`};`failed` 会在下次 run 重试。

## Two Run Modes（关键）

### A. 定时跑（无人值守，scheduled）
1. `pick-next-article.sh` 选最新一篇;若已全分发 → rest day,结束。
2. 抽一套核心文案 + 选主图,写进 `post.txt`。
3. **`syndicate.sh "$FOLDER" "$POST_TXT"`** 一把搞定扇出(slug=basename):API 平台逐个 try/catch 真发(X 先查 tweeting skill history 防双发;缺凭证降级记 `queued/no_creds`);手动平台调 `build-outbox.sh` 写 `outbox/<slug>/`(post.txt + image.png + OPEN.md)并记 `queued`。**不开浏览器**。
4. **推送通知**(PushNotification):汇总「X/Bluesky 已发✓;FB/小红书/即刻/知乎 在 outbox 等你粘」。

> 实际运行已由 launchd 在 macOS 本地每天 10:00 触发(远程 `/schedule` 拿不到本地 xurl/secrets/articles,不适用)。launchd 跑 `run-scheduled.sh` → `claude -p --allowedTools "Bash,Read,Write,Edit,Skill"`(限定工具,不用 `--dangerously-skip-permissions`)。

### B. 交互跑 `--open`（用户主动发手动平台）
- 用 `/browse` skill 打开 FB / 即刻 的 web 编辑页,把 `post.txt` 内容放进剪贴板。
- 小红书:在 Finder 弹出 `image.png`,文案进剪贴板,提示 AirDrop 到手机。
- 用户粘贴 + 点发布后,可手动跑一个 `--mark <platform>` 把 history 标成 `posted`(可选,非强制)。

## 与现有 `wjs-tweeting-from-articles` 的关系

- 那个 skill 是 **X 专用的三角度精修**(金句/比喻/反差),保留给"手动发一条精心打磨的 X thread"用。
- 本 skill 接管**每天的扇出**(含 X,用一套文案)。建议把每日 `/schedule` 档位给本 skill。
- **防双发**:本 skill 的 X 步骤,发之前**只读**(read-only)tweeting skill 的 `state/history.jsonl`,若该 slug 已被那边发过 X,则本 skill 的 X 步骤标 `skipped`。反之本 skill 也写自己的 history。两边即使都跑也不会把 X 发两遍。

## Stability Tactics 汇总

- 平台级隔离:每平台独立步骤,失败不传染。
- 幂等去重:`(slug, platform)` 为 key,可安全重跑/补发。
- 凭证降级:缺/过期凭证 → 转 outbox,不报错。
- `--dry-run`:只抽文案 + 打印每平台将发什么,不真发、不写 history。
- 凭证存 `secrets.json`(gitignore),不进任何 public repo。

## CLI 形态

```
/wjs-syndicating-articles                 # 定时/手动：选最新未分发文章，走完整 A 流程
/wjs-syndicating-articles <article-folder># 显式指定文章
/wjs-syndicating-articles --open          # B 模式：打开手动平台 web 页 + 文案进剪贴板
/wjs-syndicating-articles --dry-run       # 只草拟，不发、不写 history
/wjs-syndicating-articles --mark <slug> <platform>  # 手动标记某平台已发（可选）
```

## Daily 自动化

```
/schedule daily 10:00 /wjs-syndicating-articles
```

定时档位下走 A 模式(无人值守):发 API 平台 + 备 outbox + 推送通知。

## Out of Scope (YAGNI)

- 逐平台重写文案(已定"一套文案")。
- 浏览器自动登录并代发(违背稳定目标)。
- 微博/知乎/Medium/Mastodon 等其它平台(后续可按"有干净 API 就加 api 模式,否则加 outbox 模式"的同一框架扩展,本期不做)。
- 数据回收/互动分析。
- outbox 发布后的强制状态回写(`--mark` 为可选便利,不强制)。
