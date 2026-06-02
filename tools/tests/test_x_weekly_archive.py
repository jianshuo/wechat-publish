import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import x_weekly_archive as xa


class TimeHelpersTest(unittest.TestCase):
    def test_to_shanghai_shifts_utc_by_8h(self):
        # 13:44 UTC -> 21:44 上海同日
        dt = xa.to_shanghai("2026-06-02T13:44:57.000Z")
        self.assertEqual((dt.year, dt.month, dt.day), (2026, 6, 2))
        self.assertEqual((dt.hour, dt.minute), (21, 44))

    def test_to_shanghai_crosses_midnight_same_week(self):
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
        self.assertEqual(calls[0][1]["exclude"], "retweets")
        self.assertIn("referenced_tweets", calls[0][1]["tweet.fields"])
        self.assertIn("referenced_tweets.id", calls[0][1]["expansions"])
        # 第二次带上 token
        self.assertEqual(calls[1][1]["pagination_token"], "T2")

    def test_start_time_from_days(self):
        now = datetime.fromisoformat("2026-06-02T00:00:00+00:00")
        self.assertEqual(xa.start_time_iso(30, now), "2026-05-03T00:00:00Z")


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


class CheckPayloadTest(unittest.TestCase):
    def test_partial_errors_with_data_is_tolerated(self):
        payload = {"data": [{"id": "1"}], "errors": [{"title": "Not Found Error"}]}
        # should NOT raise
        xa.check_payload(payload)

    def test_errors_only_without_data_raises(self):
        with self.assertRaises(xa.XurlError):
            xa.check_payload({"errors": [{"title": "Not Found Error"}]})

    def test_unauthorized_raises(self):
        with self.assertRaises(xa.XurlError):
            xa.check_payload({"title": "Unauthorized", "status": 401})

    def test_clean_payload_ok(self):
        xa.check_payload({"data": [{"id": "1"}], "meta": {}})  # no raise


if __name__ == "__main__":
    unittest.main()
