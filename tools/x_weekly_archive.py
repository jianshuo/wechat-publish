"""把 X 发帖按 ISO 周归档成公众号格式文章。"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, date, timedelta, timezone
from urllib.parse import urlencode
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


def _metrics_line(tweet: dict) -> str:
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


class XurlError(RuntimeError):
    pass


def check_payload(payload: dict) -> None:
    """X API 错误判定。容忍「有 data 同时带非致命 errors」（如被引用原帖已删）。
    仅在 401/未授权、或 errors-only（无可用 data）时抛 XurlError。"""
    if not isinstance(payload, dict):
        return
    if payload.get("title") == "Unauthorized" or (isinstance(payload.get("status"), int) and payload["status"] >= 400):
        raise XurlError(f"X API 未授权/错误：{json.dumps(payload, ensure_ascii=False)[:300]}\n"
                        f"先跑 `xurl auth status` 检查认证。")
    if payload.get("errors") and not payload.get("data"):
        raise XurlError(f"X API 报错：{json.dumps(payload, ensure_ascii=False)[:300]}\n"
                        f"先跑 `xurl auth status` 检查认证。")


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
    check_payload(payload)
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
