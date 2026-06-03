# wechat-publish

王建硕公众号文章和社交分发的**产物仓库**。

这里只存「生成出来的东西」和自动化的运行状态。**写文章、发草稿、配图的逻辑不在这个 repo 里**——那些在 Claude Code 的 skill 里：`~/.claude/skills/wjs-publishing-wechat/`（含 `SKILL.md` 和 `scripts/`）。

## 目录

| 目录 | 放什么 |
|------|--------|
| `articles/` | 每篇文章一个 `YYYY-MM-DD-{slug}/` 目录，含 `article.md` / `cover.png` / `illustration.png` / `meta.json` / `content.html` / `draft.json` 等生成物 |
| `prompts/` | 各平台分发文案的 prompt（x / bluesky / threads / linkedin / facebook / 即刻 / 小红书） |
| `x-weekly/` | 每周 X 内容归档 |
| `tweet-state/` | 发推历史 `history.jsonl`（去重用） |
| `tools/` | 辅助脚本（如 `x_weekly_archive.py`） |
| `.github/workflows/tweet.yml` | 每 6 小时自动发推的 GitHub Action |
| `research/` `docs/` | 调研笔记和资料 |

## 怎么写文章

不在这里操作。直接跟 Claude Code 说：

> 帮我写一篇公众号文章，思路是…

或 `/wjs-publishing-wechat`，把草稿粘进来。skill 会润色、生成题图和解释图、输出到 `articles/`，再一行命令推草稿到 mp.weixin.qq.com。流程细节见 skill 的 `SKILL.md`。

## 改流程 / 改样式

改的是 skill，不是这个 repo：

```
~/.claude/skills/wjs-publishing-wechat/
├── SKILL.md          # 写作与发布流程
└── scripts/          # gen-cover-ai.sh / gen-illustration.sh / upload-draft.sh / pangu.py …
```
