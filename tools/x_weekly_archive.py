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
