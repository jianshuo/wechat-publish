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


if __name__ == "__main__":
    unittest.main()
