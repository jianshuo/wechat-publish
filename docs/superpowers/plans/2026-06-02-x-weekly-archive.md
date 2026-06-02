# X 发帖按周归档 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把王建硕近一个月的 X 发帖（原创+回复，含被回复/引用原帖上下文）按 ISO 周（周一～周日）归档成公众号格式的 `article.md`+`meta.json`，幂等可重跑。

**Architecture:** 单个纯函数为主的 Python 模块 `tools/x_weekly_archive.py`，分为 时间助手 / 合并分页 / 按周分组 / 渲染 / 拉取循环 / CLI 六层。X API 调用通过 `xurl --auth oauth1` 子进程完成，并被抽象成可注入的 `fetcher`，让纯逻辑可用样例 JSON 做单元测试。

**Tech Stack:** Python 3.14 标准库（`subprocess`、`json`、`datetime`、`zoneinfo`、`urllib.parse`、`unittest`）+ 系统已装的 `xurl`。无第三方依赖。

**已验证的事实（实现时不要再质疑）：**
- 用户 username = `jianshuo`，id = `999081`。
- 拉时间线必须用 `xurl --auth oauth1`（oauth2 token 返回 401）。
- 可用 endpoint：`/2/users/by/username/jianshuo`（取 id）、`/2/users/<id>/tweets`（取发帖）。
- tweets 接口参数：`start_time`、`max_results=100`、`exclude=retweets`、`tweet.fields=created_at,text,referenced_tweets,public_metrics,in_reply_to_user_id`、`expansions=referenced_tweets.id,referenced_tweets.id.author_id`、`user.fields=username`、`pagination_token`。
- 返回顶层有 `data`（主推文数组）、`includes.tweets`（被引用原帖）、`includes.users`（作者）、`meta.next_token`（翻页）。
- `created_at` 形如 `2026-06-02T13:44:57.000Z`（`datetime.fromisoformat` 在 3.11+ 可直接解析含 `Z`）。
- `referenced_tweets[].type` 取值 `replied_to` / `quoted`（`retweeted` 已被 `exclude=retweets` 滤掉）。

**文件结构：**
- 创建 `tools/x_weekly_archive.py` —— 全部逻辑 + CLI。
- 创建 `tools/tests/test_x_weekly_archive.py` —— unittest 单测（注入假 fetcher / 样例 JSON）。
- 运行产出目录 `x-weekly/`（脚本运行时自动创建，不在本计划提交）。

**测试运行约定：** 测试文件顶部插入 `sys.path`，直接 `python3 tools/tests/test_x_weekly_archive.py` 跑（无 pytest）。

---

### Task 1: 模块骨架 + 时间助手

**Files:**
- Create: `tools/x_weekly_archive.py`
- Test: `tools/tests/test_x_weekly_archive.py`

- [ ] **Step 1: 写失败测试**

`tools/tests/test_x_weekly_archive.py`:
```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import x_weekly_archive as xa


class TimeHelpersTest(unittest.TestCase):
    def test_to_shanghai_shifts_utc_by_8h(self):
        # 13:44 UTC -> 21:44 上海同日
        dt = xa.to_shanghai("2026-06-02T13:44:57.000Z")
        self.assertEqual((dt.year, dt.month, dt.day), (2026, 6, 2))
        self.assertEqual((dt.hour, dt.minute), (21, 44))

    def test_to_shanghai_crosses_midnight_changes_week(self):
        # 2026-06-01 17:00 UTC = 周一 6/2 01:00 上海 -> 属于含 6/2 的那一周
        dt = xa.to_shanghai("2026-06-01T17:00:00.000Z")
        self.assertEqual((dt.month, dt.day, dt.hour), (6, 2, 1))

    def test_iso_week_key_and_monday(self):
        dt = xa.to_shanghai("2026-06-02T13:44:57.000Z")  # 周二
        key = xa.iso_week_key(dt)
        self.assertEqual(len(key), 2)
        monday = xa.week_monday(*key)
        self.assertEqual(monday.weekday(), 0)  # 周一
        self.assertLessEqual(monday, dt.date())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 tools/tests/test_x_weekly_archive.py`
Expected: FAIL —— `ModuleNotFoundError: No module named 'x_weekly_archive'`

- [ ] **Step 3: 写最小实现**

`tools/x_weekly_archive.py`:
```python
"""把 X 发帖按 ISO 周归档成公众号格式文章。"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

SHANGHAI = ZoneInfo("Asia/Shanghai")


def to_shanghai(created_at: str) -> datetime:
    """把 X 的 created_at（UTC，含 Z）转成上海时区 aware datetime。"""
    dt = datetime.fromisoformat(created_at)  # 3.11+ 可解析末尾 Z
    return dt.astimezone(SHANGHAI)


def iso_week_key(dt: datetime) -> tuple[int, int]:
    """返回 (iso_year, iso_week)。"""
    cal = dt.isocalendar()
    return (cal[0], cal[1])


def week_monday(iso_year: int, iso_week: int) -> date:
    """该 ISO 周的周一日期。"""
    return date.fromisocalendar(iso_year, iso_week, 1)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 tools/tests/test_x_weekly_archive.py`
Expected: PASS（3 tests）

- [ ] **Step 5: 提交**

```bash
cd /Users/jianshuo/code/wechat-publish
git add tools/x_weekly_archive.py tools/tests/test_x_weekly_archive.py
git commit -m "feat(x-archive): 时间助手与模块骨架"
```

---

### Task 2: 合并分页 merge_pages

**Files:**
- Modify: `tools/x_weekly_archive.py`
- Test: `tools/tests/test_x_weekly_archive.py`

- [ ] **Step 1: 写失败测试**（在 `TimeHelpersTest` 类之后追加新类）

```python
class MergePagesTest(unittest.TestCase):
    def test_merges_data_and_includes_across_pages(self):
        pages = [
            {
                "data": [{"id": "1", "text": "a", "created_at": "2026-06-02T01:00:00.000Z"}],
                "includes": {
                    "tweets": [{"id": "p1", "text": "parent1", "author_id": "u9"}],
                    "users": [{"id": "u9", "username": "alice"}],
                },
                "meta": {"next_token": "T2"},
            },
            {
                "data": [{"id": "2", "text": "b", "created_at": "2026-06-03T01:00:00.000Z"}],
                "includes": {"tweets": [], "users": []},
                "meta": {},
            },
        ]
        merged = xa.merge_pages(pages)
        self.assertEqual([t["id"] for t in merged["data"]], ["1", "2"])
        self.assertEqual(merged["tweets_by_id"]["p1"]["text"], "parent1")
        self.assertEqual(merged["users_by_id"]["u9"]["username"], "alice")

    def test_handles_missing_keys(self):
        merged = xa.merge_pages([{}])
        self.assertEqual(merged["data"], [])
        self.assertEqual(merged["tweets_by_id"], {})
        self.assertEqual(merged["users_by_id"], {})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 tools/tests/test_x_weekly_archive.py`
Expected: FAIL —— `AttributeError: module ... has no attribute 'merge_pages'`

- [ ] **Step 3: 写最小实现**（追加到模块末尾）

```python
def merge_pages(pages: list[dict]) -> dict:
    """把多页 API 响应合并成 {data, tweets_by_id, users_by_id}。"""
    data: list[dict] = []
    tweets_by_id: dict[str, dict] = {}
    users_by_id: dict[str, dict] = {}
    for page in pages:
        data.extend(page.get("data") or [])
        includes = page.get("includes") or {}
        for tweet in includes.get("tweets") or []:
            tweets_by_id[tweet["id"]] = tweet
        for user in includes.get("users") or []:
            users_by_id[user["id"]] = user
    return {"data": data, "tweets_by_id": tweets_by_id, "users_by_id": users_by_id}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 tools/tests/test_x_weekly_archive.py`
Expected: PASS（5 tests）

- [ ] **Step 5: 提交**

```bash
cd /Users/jianshuo/code/wechat-publish
git add tools/x_weekly_archive.py tools/tests/test_x_weekly_archive.py
git commit -m "feat(x-archive): 合并分页响应"
```

---

### Task 3: 按周分组 group_by_week

**Files:**
- Modify: `tools/x_weekly_archive.py`
- Test: `tools/tests/test_x_weekly_archive.py`

- [ ] **Step 1: 写失败测试**

```python
class GroupByWeekTest(unittest.TestCase):
    def test_groups_into_weeks_sorted_ascending(self):
        merged = {
            "data": [
                {"id": "late", "text": "z", "created_at": "2026-06-03T02:00:00.000Z"},
                {"id": "early", "text": "a", "created_at": "2026-06-02T02:00:00.000Z"},
                {"id": "nextwk", "text": "n", "created_at": "2026-06-09T02:00:00.000Z"},
            ],
            "tweets_by_id": {},
            "users_by_id": {},
        }
        buckets = xa.group_by_week(merged)
        self.assertEqual(len(buckets), 2)
        # 第一周桶内按时间正序：early 在 late 前
        first_week = xa.iso_week_key(xa.to_shanghai("2026-06-02T02:00:00.000Z"))
        ids = [tweet["id"] for _, tweet in buckets[first_week]]
        self.assertEqual(ids, ["early", "late"])
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 tools/tests/test_x_weekly_archive.py`
Expected: FAIL —— 无 `group_by_week`

- [ ] **Step 3: 写最小实现**（追加到模块末尾）

```python
def group_by_week(merged: dict) -> dict[tuple[int, int], list[tuple[datetime, dict]]]:
    """按上海时区 ISO 周分桶；桶内按时间正序。键=(iso_year, iso_week)。"""
    buckets: dict[tuple[int, int], list[tuple[datetime, dict]]] = {}
    for tweet in merged["data"]:
        local = to_shanghai(tweet["created_at"])
        key = iso_week_key(local)
        buckets.setdefault(key, []).append((local, tweet))
    for key in buckets:
        buckets[key].sort(key=lambda pair: pair[0])
    return buckets
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 tools/tests/test_x_weekly_archive.py`
Expected: PASS（6 tests）

- [ ] **Step 5: 提交**

```bash
cd /Users/jianshuo/code/wechat-publish
git add tools/x_weekly_archive.py tools/tests/test_x_weekly_archive.py
git commit -m "feat(x-archive): 按周分组"
```

---

### Task 4: 渲染一周 render_week

**Files:**
- Modify: `tools/x_weekly_archive.py`
- Test: `tools/tests/test_x_weekly_archive.py`

- [ ] **Step 1: 写失败测试**

```python
class RenderWeekTest(unittest.TestCase):
    def _merged(self):
        return {
            "tweets_by_id": {"p1": {"id": "p1", "text": "原帖很长" * 30, "author_id": "u9"}},
            "users_by_id": {"u9": {"id": "u9", "username": "alice"}},
        }

    def test_renders_folder_meta_and_reply_context(self):
        key = xa.iso_week_key(xa.to_shanghai("2026-06-02T13:44:57.000Z"))
        items = [
            (xa.to_shanghai("2026-06-02T13:44:57.000Z"),
             {"id": "1", "text": "原创一条",
              "public_metrics": {"like_count": 2, "reply_count": 1, "retweet_count": 0}}),
            (xa.to_shanghai("2026-06-02T14:00:00.000Z"),
             {"id": "2", "text": "我的回复",
              "referenced_tweets": [{"type": "replied_to", "id": "p1"}],
              "public_metrics": {"like_count": 0, "reply_count": 0, "retweet_count": 0}}),
        ]
        folder, md, meta = xa.render_week(key, items, self._merged(), include_metrics=True)

        self.assertTrue(folder.endswith("-x-week-23"))   # 2026-W23
        self.assertTrue(folder.startswith("2026-06-01"))  # 该周周一
        self.assertEqual(meta["author"], "王建硕")
        self.assertEqual(meta["date"], "2026-06-01")
        self.assertEqual(meta["slug"], "x-week-23")
        self.assertIn("X 周记", meta["title"])
        self.assertIn("# X 周记", md)
        self.assertIn("原创一条", md)
        self.assertIn("↩️ 回复 @alice", md)   # 回复带上下文
        self.assertIn("21:44", md)             # 本地时间
        self.assertIn("♥", md)                 # 互动数

    def test_no_metrics_when_disabled(self):
        key = xa.iso_week_key(xa.to_shanghai("2026-06-02T13:44:57.000Z"))
        items = [(xa.to_shanghai("2026-06-02T13:44:57.000Z"),
                  {"id": "1", "text": "x", "public_metrics": {"like_count": 9, "reply_count": 0, "retweet_count": 0}})]
        _, md, _ = xa.render_week(key, items, self._merged(), include_metrics=False)
        self.assertNotIn("♥", md)

    def test_reply_to_deleted_parent_degrades(self):
        key = xa.iso_week_key(xa.to_shanghai("2026-06-02T13:44:57.000Z"))
        items = [(xa.to_shanghai("2026-06-02T13:44:57.000Z"),
                  {"id": "2", "text": "回复", "referenced_tweets": [{"type": "replied_to", "id": "GONE"}]})]
        _, md, _ = xa.render_week(key, items, self._merged(), include_metrics=False)
        self.assertIn("↩️ 回复", md)  # 不崩，降级展示
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 tools/tests/test_x_weekly_archive.py`
Expected: FAIL —— 无 `render_week`

- [ ] **Step 3: 写最小实现**（追加到模块末尾）

```python
WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
REF_LABEL = {"replied_to": "↩️ 回复", "quoted": "🔁 引用"}


def _snippet(text: str, limit: int = 80) -> str:
    """压成一行并截断。"""
    one_line = " ".join(text.split())
    return one_line if len(one_line) <= limit else one_line[:limit] + "…"


def _ref_lines(tweet: dict, merged: dict) -> list[str]:
    """渲染被回复/引用原帖上下文（可能多条）。"""
    lines: list[str] = []
    for ref in tweet.get("referenced_tweets") or []:
        label = REF_LABEL.get(ref.get("type"))
        if not label:
            continue
        parent = merged["tweets_by_id"].get(ref.get("id"))
        if parent:
            author = merged["users_by_id"].get(parent.get("author_id", ""), {})
            handle = author.get("username", "?")
            lines.append(f"> {label} @{handle}：{_snippet(parent.get('text', ''))}")
        else:
            lines.append(f"> {label}（原帖不可见）")
    return lines


def _metrics_line(tweet: dict) -> str | None:
    pm = tweet.get("public_metrics") or {}
    return (f"<small>💬{pm.get('reply_count', 0)} "
            f"♥{pm.get('like_count', 0)} "
            f"🔁{pm.get('retweet_count', 0)}</small>")


def render_week(key: tuple[int, int], items: list[tuple[datetime, dict]],
                merged: dict, include_metrics: bool = True) -> tuple[str, str, dict]:
    """返回 (folder_name, article_md, meta_dict)。"""
    iso_year, iso_week = key
    monday = week_monday(iso_year, iso_week)
    sunday = monday + timedelta(days=6)
    title = f"X 周记 · {monday.month}月{monday.day}日–{sunday.month}月{sunday.day}日"

    lines: list[str] = [f"# {title}", "",
                        f"> 本周在 X 上的发帖归档（原创 + 回复），共 {len(items)} 条。", ""]
    current_day = None
    for local, tweet in items:
        day = local.date()
        if day != current_day:
            current_day = day
            lines.append(f"## {WEEKDAYS[local.weekday()]} {day.month}月{day.day}日")
            lines.append("")
        for ref_line in _ref_lines(tweet, merged):
            lines.append(ref_line)
        lines.append(f"**{local.strftime('%H:%M')}**　{tweet.get('text', '')}")
        if include_metrics:
            lines.append(_metrics_line(tweet))
        lines.append("")

    article_md = "\n".join(lines).rstrip() + "\n"
    meta = {
        "title": title,
        "summary": f"本周在 X 上的 {len(items)} 条发帖（原创 + 回复）归档。",
        "author": "王建硕",
        "date": monday.isoformat(),
        "slug": f"x-week-{iso_week:02d}",
    }
    folder_name = f"{monday.isoformat()}-x-week-{iso_week:02d}"
    return folder_name, article_md, meta
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 tools/tests/test_x_weekly_archive.py`
Expected: PASS（9 tests）

- [ ] **Step 5: 提交**

```bash
cd /Users/jianshuo/code/wechat-publish
git add tools/x_weekly_archive.py tools/tests/test_x_weekly_archive.py
git commit -m "feat(x-archive): 渲染周文章（含回复/引用上下文与互动数）"
```

---

### Task 5: 拉取循环 fetch_all（注入式 fetcher）

**Files:**
- Modify: `tools/x_weekly_archive.py`
- Test: `tools/tests/test_x_weekly_archive.py`

- [ ] **Step 1: 写失败测试**

```python
class FetchAllTest(unittest.TestCase):
    def test_paginates_until_no_next_token(self):
        calls = []

        def fake_fetcher(user_id, params):
            calls.append((user_id, dict(params)))
            if "pagination_token" not in params:
                return {"data": [{"id": "1", "text": "a", "created_at": "2026-06-02T01:00:00.000Z"}],
                        "meta": {"next_token": "T2"}}
            return {"data": [{"id": "2", "text": "b", "created_at": "2026-06-03T01:00:00.000Z"}],
                    "meta": {}}

        merged = xa.fetch_all("999081", "2026-05-03T00:00:00Z", fake_fetcher)
        self.assertEqual([t["id"] for t in merged["data"]], ["1", "2"])
        self.assertEqual(len(calls), 2)
        # 首次调用带 start_time、不带 pagination_token
        self.assertEqual(calls[0][1]["start_time"], "2026-05-03T00:00:00Z")
        self.assertNotIn("pagination_token", calls[0][1])
        # 第二次带上 token
        self.assertEqual(calls[1][1]["pagination_token"], "T2")

    def test_start_time_from_days(self):
        now = datetime.fromisoformat("2026-06-02T00:00:00+00:00")
        self.assertEqual(xa.start_time_iso(30, now), "2026-05-03T00:00:00Z")
```

（在测试文件顶部确保已 `from datetime import datetime`。）

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 tools/tests/test_x_weekly_archive.py`
Expected: FAIL —— 无 `fetch_all` / `start_time_iso`

- [ ] **Step 3: 写最小实现**（追加到模块末尾）

```python
def start_time_iso(days: int, now_utc: datetime) -> str:
    """now - days，格式化为 X API 要的 UTC 秒级 ISO。"""
    start = now_utc - timedelta(days=days)
    return start.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_all(user_id: str, start_time: str, fetcher) -> dict:
    """用注入的 fetcher(user_id, params)->dict 翻页拉完，返回 merge_pages 结果。"""
    base_params = {
        "start_time": start_time,
        "max_results": "100",
        "exclude": "retweets",
        "tweet.fields": "created_at,text,referenced_tweets,public_metrics,in_reply_to_user_id",
        "expansions": "referenced_tweets.id,referenced_tweets.id.author_id",
        "user.fields": "username",
    }
    pages: list[dict] = []
    token = None
    while True:
        params = dict(base_params)
        if token:
            params["pagination_token"] = token
        page = fetcher(user_id, params)
        pages.append(page)
        token = (page.get("meta") or {}).get("next_token")
        if not token:
            break
    return merge_pages(pages)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 tools/tests/test_x_weekly_archive.py`
Expected: PASS（11 tests）

- [ ] **Step 5: 提交**

```bash
cd /Users/jianshuo/code/wechat-publish
git add tools/x_weekly_archive.py tools/tests/test_x_weekly_archive.py
git commit -m "feat(x-archive): 翻页拉取循环"
```

---

### Task 6: 真实 xurl 调用 + CLI main

**Files:**
- Modify: `tools/x_weekly_archive.py`

说明：子进程与文件写盘部分不做单元测试（靠 Task 7 冒烟测试覆盖）。本任务只加实现并人工自测。

- [ ] **Step 1: 追加 xurl 封装、id 查询、写盘、CLI（追加到模块末尾）**

```python
import argparse
import json
import os
import subprocess
import sys
from datetime import timezone
from urllib.parse import urlencode


class XurlError(RuntimeError):
    pass


def run_xurl(path: str) -> dict:
    """用 oauth1 调 xurl，返回解析后的 JSON。失败抛 XurlError。"""
    proc = subprocess.run(
        ["xurl", "--auth", "oauth1", path],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise XurlError(f"xurl 退出码 {proc.returncode}: {proc.stderr.strip()}\n"
                        f"先跑 `xurl auth status` 检查认证。")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise XurlError(f"xurl 返回非 JSON：{proc.stdout[:200]}") from exc
    if isinstance(payload, dict) and (payload.get("errors") or payload.get("title") == "Unauthorized"):
        raise XurlError(f"X API 报错：{json.dumps(payload, ensure_ascii=False)[:300]}\n"
                        f"先跑 `xurl auth status` 检查认证。")
    return payload


def get_user_id(username: str) -> str:
    payload = run_xurl(f"/2/users/by/username/{username}")
    return payload["data"]["id"]


def real_fetcher(user_id: str, params: dict) -> dict:
    query = urlencode(params)
    return run_xurl(f"/2/users/{user_id}/tweets?{query}")


def write_week(out_dir: str, folder_name: str, article_md: str, meta: dict) -> str:
    week_dir = os.path.join(out_dir, folder_name)
    os.makedirs(week_dir, exist_ok=True)
    with open(os.path.join(week_dir, "article.md"), "w", encoding="utf-8") as fh:
        fh.write(article_md)
    with open(os.path.join(week_dir, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return week_dir


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="把 X 发帖按周归档成公众号格式文章")
    parser.add_argument("--days", type=int, default=30, help="往前拉多少天（默认 30）")
    parser.add_argument("--username", default="jianshuo", help="X 用户名")
    parser.add_argument("--out", default="x-weekly", help="输出目录")
    parser.add_argument("--no-metrics", action="store_true", help="不显示互动数")
    args = parser.parse_args(argv)

    now_utc = datetime.now(timezone.utc)
    start_time = start_time_iso(args.days, now_utc)
    print(f"拉取 @{args.username} 自 {start_time} 起的发帖（原创+回复，去转推）…")

    try:
        user_id = get_user_id(args.username)
        merged = fetch_all(user_id, start_time, real_fetcher)
    except XurlError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    # 原始数据落盘便于排查
    cache_dir = os.path.join(args.out, ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    stamp = now_utc.strftime("%Y%m%dT%H%M%SZ")
    with open(os.path.join(cache_dir, f"tweets-{stamp}.json"), "w", encoding="utf-8") as fh:
        json.dump(merged, fh, ensure_ascii=False, indent=2)

    buckets = group_by_week(merged)
    if not buckets:
        print("窗口内没有发帖，未生成任何文章。")
        return 0

    for key in sorted(buckets):
        items = buckets[key]
        folder_name, article_md, meta = render_week(
            key, items, merged, include_metrics=not args.no_metrics)
        week_dir = write_week(args.out, folder_name, article_md, meta)
        print(f"  写入 {week_dir}（{len(items)} 条）")

    print(f"完成，共 {len(buckets)} 周。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: 确认单测仍全绿（没破坏纯逻辑）**

Run: `python3 tools/tests/test_x_weekly_archive.py`
Expected: PASS（11 tests）

- [ ] **Step 3: 语法/导入自检**

Run: `python3 -c "import sys; sys.path.insert(0,'tools'); import x_weekly_archive; print('ok')"`
Expected: 打印 `ok`

- [ ] **Step 4: 提交**

```bash
cd /Users/jianshuo/code/wechat-publish
git add tools/x_weekly_archive.py
git commit -m "feat(x-archive): xurl 调用与 CLI main"
```

---

### Task 7: 端到端冒烟 + 归档目录配置

**Files:**
- Modify: `.gitignore`
- 运行产出：`x-weekly/`

- [ ] **Step 1: 忽略缓存目录**

在 `.gitignore` 末尾追加：
```
# X 归档脚本的原始数据缓存（可重新拉取）
x-weekly/.cache/
```

- [ ] **Step 2: 真跑一次（最近 30 天）**

Run: `cd /Users/jianshuo/code/wechat-publish && python3 tools/x_weekly_archive.py --days 30`
Expected: 打印拉取进度，逐周「写入 x-weekly/YYYY-MM-DD-x-week-WW（N 条）」，结尾「完成，共 K 周。」

- [ ] **Step 3: 人工核对产出**

Run: `ls x-weekly/ && echo '---' && cat "$(ls -dt x-weekly/*/ | head -1)article.md"`
Expected: 看到按周文件夹；最新一周 `article.md` 是 `# X 周记 …`，按天分组，回复显示 `> ↩️ 回复 @… ：…`，每条带本地时间与互动数。核对至少一条回复的上下文是否正确、时间是否为上海时区。

- [ ] **Step 4: 提交产出与忽略规则**

```bash
cd /Users/jianshuo/code/wechat-publish
git add .gitignore x-weekly
git commit -m "chore(x-archive): 首次归档近一个月 X 发帖 + 忽略缓存"
```

---

## 自检（Self-Review）

- **Spec 覆盖：** 来源/拉取(Task5,6)、原创+回复去转推(`exclude=retweets`，Task5)、上海时区 ISO 周(Task1,3)、公众号格式输出(Task4,6)、回复带原帖上下文(Task4)、幂等重写(Task6 `write_week` 以 `exist_ok`+整文件覆盖)、缓存(Task6)、错误处理(Task6 `XurlError`)、CLI 参数(Task6)、冒烟(Task7) —— 均有任务覆盖。引用(`quoted`)上下文为 spec 确认的额外项，并入 Task4。
- **占位符扫描：** 无 TBD/TODO；每段代码完整。
- **命名一致性：** `to_shanghai`/`iso_week_key`/`week_monday`/`merge_pages`/`group_by_week`/`render_week`/`start_time_iso`/`fetch_all`/`real_fetcher`/`run_xurl`/`get_user_id`/`write_week`/`main` 在各任务间签名一致；`render_week` 返回 `(folder_name, article_md, meta)` 三元组在 Task4 定义、Task6 消费时解构一致。
- **幂等说明：** `write_week` 用固定 `folder_name`（含周一日期+周号）整文件覆盖，落在窗口内的周重写、窗口外不动 —— 符合 spec「本周随发帖增长、历史周稳定」。
- **测试编号：** Task1=3、Task2=+2=5、Task3=+1=6、Task4=+3=9、Task5=+2=11，与各步「Expected」累计数一致。
