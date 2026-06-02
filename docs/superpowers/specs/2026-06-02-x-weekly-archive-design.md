# X 发帖按周归档 —— 设计文档

日期：2026-06-02
作者：王建硕（设计协作：Claude Code）

## 目标

把王建硕在 X（Twitter）上的发帖，按「每周一篇」的方式归档成文章保存下来。
范围是**最近一个月开始往后**，不求全量历史。每篇收**原创帖 + 回复**（不含转推），
回复要带上被回复原帖的上下文。文章套用现有公众号文章的存储格式。

## 范围与决定（已与用户确认）

- **时间范围**：运行时刻往前约 30 天，之后随手重跑即可继续累积。
- **帖子范围**：原创 + 回复，去掉转推（`exclude=retweets`）。
- **周边界**：ISO 周，周一到周日。
- **时区**：按 Asia/Shanghai 计算「哪一天 / 哪一周」。
- **输出位置**：单独目录 `x-weekly/`，不与现有 `articles/` 混放。
- **输出格式**：每周一个文件夹，含 `article.md` + `meta.json`，与现有文章结构一致。
- **回复上下文**：带上被回复原帖的作者与文本。
- **运行方式**：方案 A —— 可复用脚本 `tools/x-weekly-archive.py`，幂等可重跑。

## 架构

单个 Python3 脚本 `tools/x-weekly-archive.py`，依赖标准库 + 系统已安装的 `xurl`。
无第三方包（时区用 `zoneinfo`）。分四个清晰单元：

1. **fetch** —— 通过 `xurl` 调 X API 拉推文（含分页、含 expansions）。
2. **group** —— 把推文按上海时区的 ISO 周（周一～周日）分桶。
3. **render** —— 每个周桶渲染成 `article.md` + `meta.json`。
4. **main** —— 串联，处理参数、缓存、幂等写盘、错误。

### 1. fetch

- `xurl /2/users/me` → 解析出 `data.id`（用户 id）。
- 循环调用：
  ```
  xurl "/2/users/:id/tweets?\
  start_time=<ISO8601 UTC，now-30d>&\
  max_results=100&\
  exclude=retweets&\
  tweet.fields=created_at,text,referenced_tweets,public_metrics,in_reply_to_user_id&\
  expansions=referenced_tweets.id,referenced_tweets.id.author_id,author_id&\
  user.fields=username&\
  pagination_token=<上一页 meta.next_token>"
  ```
- 翻页直到没有 `meta.next_token`。
- 合并所有页的 `data`（主推文）与 `includes.tweets` / `includes.users`（被引用原帖及作者），
  建立 `id → tweet` 和 `id → username` 的查找表，供 render 解析回复上下文。
- 把合并后的原始 JSON 存一份到 `x-weekly/.cache/tweets-<UTC时间戳>.json` 便于排查。

### 2. group

- 对每条推 `created_at`（UTC）→ `datetime` → 转 `Asia/Shanghai`。
- 取 `isocalendar()` 得 `(iso_year, iso_week, iso_weekday)`。
- 以 `(iso_year, iso_week)` 为键分桶；桶内按时间**正序**。
- 同时算出该周周一的本地日期（用于文件夹名与 meta.date）。

### 3. render

每个周桶产出文件夹 `x-weekly/YYYY-MM-DD-x-week-WW/`：
- `YYYY-MM-DD` = 该周周一（上海时区）。
- `WW` = 两位 ISO 周号。

`article.md`：
```
# X 周记 · M月D日–M月D日（共 N 条）

> 本周在 X 上的发帖归档（原创 + 回复）。

## 周一 6月2日

**14:32**
<原创帖正文>

↩️ 回复 @someuser：<被回复原帖的一句话>
**15:01**
<我的回复正文>

...
```
- 每条带本地时间 `HH:MM`。
- 原创帖直接成段。
- 回复：先用引用前缀 `↩️ 回复 @<username>：<原帖文本，截断到约 80 字>`，再列我的回复正文。
  若原帖在 `includes` 里找不到（已删/不可见），降级为 `↩️ 回复 @<username>`。
- 互动数（赞/转/回复）作为可选小字尾注，默认开启，低调呈现。

`meta.json`：
```json
{
  "title": "X 周记 · 6月2日–6月8日",
  "summary": "本周在 X 上的 N 条发帖（原创 + 回复）归档。",
  "author": "王建硕",
  "date": "2026-06-02",
  "slug": "x-week-23"
}
```

### 4. main / 幂等

- 参数：`--days N`（默认 30）、`--out <dir>`（默认 `x-weekly`）、`--no-metrics`。
- 幂等：**以周文件夹为单位整体重写**。落在拉取窗口内的周会被重新生成；窗口外的历史周不动。
  - 效果：当前「本周」那篇会随发帖不断更新；已封存的历史周稳定。
- 某周 0 条 → 不生成空文件夹。

## 错误处理

- `xurl` 返回非 0 或响应含 `errors` / `title=Unauthorized` → 打印清晰错误，提示运行 `xurl auth status` 检查认证。
- 限流（429）→ 报错并提示稍后重试（首版不做自动退避重试，保持简单；如命中再加）。
- `/2/users/me` 取不到 id → 直接退出并报错。
- 时区库缺失（理论上 3.9+ 自带 `zoneinfo`）→ 提示升级 Python。

## 测试

- **fetch**：用一份保存的样例响应 JSON 做夹具，验证分页合并与查找表构建（把 `xurl` 调用抽成可注入的函数，测试时喂假数据）。
- **group**：构造跨周、跨年末（ISO 周边界）、跨午夜（时区导致换周）的样例，验证分桶正确。
- **render**：给定一个周桶，验证 `article.md` / `meta.json` 内容与回复上下文渲染（含原帖缺失降级）。
- **冒烟**：真跑一次 `python3 tools/x-weekly-archive.py --days 30`，人工核对生成的文件夹。

## 非目标（YAGNI）

- 不做全量历史回填（>30 天、>3200 条）。
- 不自动发布到公众号 / 任何平台（仅本地归档）。
- 不做定时自动化（以后想要再用 /schedule 挂，不在本次范围）。
- 不抓媒体附件（图片/视频）——首版只存文字与原帖上下文。
