import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import x_tweet_playground as xp


class CacheSelectionTest(unittest.TestCase):
    def test_latest_cache_file_uses_newest_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_path = os.path.join(tmp, "tweets-old.json")
            new_path = os.path.join(tmp, "tweets-new.json")
            with open(old_path, "w", encoding="utf-8") as fh:
                fh.write("{}")
            with open(new_path, "w", encoding="utf-8") as fh:
                fh.write("{}")
            os.utime(old_path, (100, 100))
            os.utime(new_path, (200, 200))

            self.assertEqual(xp.latest_cache_file(tmp), new_path)

    def test_latest_cache_file_raises_for_missing_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(xp.PlaygroundError):
                xp.latest_cache_file(tmp)


class TweetLoadingTest(unittest.TestCase):
    def _write_cache(self, payload):
        tmp = tempfile.TemporaryDirectory()
        path = os.path.join(tmp.name, "tweets.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        self.addCleanup(tmp.cleanup)
        return path

    def test_filters_replies_keeps_quote_tweets_and_sorts(self):
        cache_path = self._write_cache({
            "data": [
                {
                    "id": "3",
                    "created_at": "2026-06-02T03:00:00.000Z",
                    "text": "reply via referenced_tweets",
                    "referenced_tweets": [{"type": "replied_to", "id": "p1"}],
                },
                {
                    "id": "2",
                    "created_at": "2026-06-02T02:00:00.000Z",
                    "text": "quote stays",
                    "referenced_tweets": [{"type": "quoted", "id": "q1"}],
                    "public_metrics": {"like_count": 4, "reply_count": 1, "retweet_count": 0},
                },
                {
                    "id": "4",
                    "created_at": "2026-06-02T04:00:00.000Z",
                    "text": "reply via in_reply_to_user_id",
                    "in_reply_to_user_id": "999081",
                },
                {
                    "id": "1",
                    "created_at": "2026-06-02T01:00:00.000Z",
                    "text": "plain tweet",
                },
            ]
        })

        tweets = xp.load_tweets_from_cache(cache_path)

        self.assertEqual([tweet["id"] for tweet in tweets], ["1", "2"])
        self.assertEqual(tweets[0]["kind"], "tweet")
        self.assertEqual(tweets[1]["kind"], "quote")
        self.assertEqual(tweets[1]["metrics"]["like_count"], 4)
        self.assertEqual(tweets[1]["url"], "https://x.com/jianshuo/status/2")

    def test_load_tweets_from_weekly_articles_filters_replies(self):
        with tempfile.TemporaryDirectory() as tmp:
            week_dir = os.path.join(tmp, "x-weekly", "2026-06-01-x-week-23")
            os.makedirs(week_dir)
            with open(os.path.join(week_dir, "article.md"), "w", encoding="utf-8") as fh:
                fh.write(
                    "# X 周记 · 6月1日–6月7日\n\n"
                    "## 周一 6月1日\n\n"
                    "**09:00**\u3000plain tweet\n"
                    "<small>💬1 ♥2 🔁0</small>\n\n"
                    "> ↩️ 回复 @someone：parent\n"
                    "**10:00**\u3000reply tweet\n"
                    "<small>💬0 ♥0 🔁0</small>\n\n"
                    "> 🔁 引用 @someone：quoted\n"
                    "**11:00**\u3000quote tweet https://t.co/abc\n"
                    "<small>💬3 ♥4 🔁1</small>\n"
                )

            tweets = xp.load_tweets_from_weekly_articles(tmp)

        self.assertEqual([tweet["text"] for tweet in tweets], ["plain tweet", "quote tweet https://t.co/abc"])
        self.assertEqual([tweet["kind"] for tweet in tweets], ["tweet", "quote"])
        self.assertEqual(tweets[0]["created_at"], "2026-06-01T09:00:00")
        self.assertEqual(tweets[1]["metrics"]["like_count"], 4)


class RewriteParsingTest(unittest.TestCase):
    def test_parse_rewrite_response_accepts_versions(self):
        parsed = xp.parse_rewrite_response(
            '{"versions":[{"id":"1","text":"A"},{"id":"2","text":"B"}]}',
            ["1", "2"],
        )

        self.assertEqual(parsed, [{"id": "1", "text": "A"}, {"id": "2", "text": "B"}])

    def test_parse_rewrite_response_rejects_missing_id(self):
        with self.assertRaises(xp.PlaygroundError):
            xp.parse_rewrite_response('{"versions":[{"id":"1","text":"A"}]}', ["1", "2"])

    def test_build_openai_payload_contains_model_prompt_and_ids(self):
        payload = xp.build_openai_payload(
            "gpt-test",
            "make it sharper",
            [{"id": "1", "text": "hello"}, {"id": "2", "text": "world"}],
        )

        self.assertEqual(payload["model"], "gpt-test")
        self.assertIn("valid JSON", payload["instructions"])
        self.assertIn("make it sharper", payload["input"])
        self.assertIn('"id": "1"', payload["input"])
        self.assertIn('"id": "2"', payload["input"])


if __name__ == "__main__":
    unittest.main()
