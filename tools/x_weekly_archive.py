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
