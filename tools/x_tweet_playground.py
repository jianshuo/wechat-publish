"""Local playground for rewriting archived X tweets."""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import request


class PlaygroundError(RuntimeError):
    """User-facing error for playground operations."""


def latest_cache_file(cache_dir: str | Path) -> str:
    """Return the newest x-weekly cache file by mtime."""
    cache_path = Path(cache_dir)
    candidates = list(cache_path.glob("tweets-*.json"))
    if not candidates:
        raise PlaygroundError(f"No tweet cache files found in {cache_path}")
    return str(max(candidates, key=lambda path: path.stat().st_mtime))


def tweet_url(tweet_id: str) -> str:
    return f"https://x.com/jianshuo/status/{tweet_id}"


def is_reply(tweet: dict[str, Any]) -> bool:
    if tweet.get("in_reply_to_user_id"):
        return True
    return any(
        ref.get("type") == "replied_to"
        for ref in tweet.get("referenced_tweets") or []
    )


def normalize_tweet(tweet: dict[str, Any]) -> dict[str, Any]:
    refs = tweet.get("referenced_tweets") or []
    kind = "quote" if any(ref.get("type") == "quoted" for ref in refs) else "tweet"
    metrics = tweet.get("public_metrics") or {}
    return {
        "id": str(tweet["id"]),
        "created_at": tweet.get("created_at", ""),
        "text": tweet.get("text", ""),
        "url": tweet_url(str(tweet["id"])),
        "metrics": {
            "reply_count": int(metrics.get("reply_count", 0) or 0),
            "like_count": int(metrics.get("like_count", 0) or 0),
            "retweet_count": int(metrics.get("retweet_count", 0) or 0),
        },
        "kind": kind,
    }


def load_tweets_from_cache(cache_path: str | Path) -> list[dict[str, Any]]:
    with open(cache_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    data = payload.get("data")
    if not isinstance(data, list):
        raise PlaygroundError(f"Cache file does not contain data[]: {cache_path}")
    tweets = [normalize_tweet(tweet) for tweet in data if not is_reply(tweet)]
    tweets.sort(key=lambda tweet: tweet["created_at"])
    return tweets


def load_latest_tweets(root_dir: str | Path) -> list[dict[str, Any]]:
    root = Path(root_dir)
    article_tweets = load_tweets_from_weekly_articles(root)
    if article_tweets:
        return article_tweets
    cache_path = latest_cache_file(root / "x-weekly" / ".cache")
    return load_tweets_from_cache(cache_path)


METRICS_RE = re.compile(r"💬(\d+)\s+♥(\d+)\s+🔁(\d+)")
TIME_RE = re.compile(r"^\*\*(\d{2}):(\d{2})\*\*\s*[　 ](.*)$")
DAY_RE = re.compile(r"^##\s+\S+\s+(\d+)月(\d+)日")


def parse_metrics(line: str) -> dict[str, int]:
    match = METRICS_RE.search(line)
    if not match:
        return {"reply_count": 0, "like_count": 0, "retweet_count": 0}
    return {
        "reply_count": int(match.group(1)),
        "like_count": int(match.group(2)),
        "retweet_count": int(match.group(3)),
    }


def load_tweets_from_weekly_articles(root_dir: str | Path) -> list[dict[str, Any]]:
    """Parse all x-weekly article.md files, excluding reply entries."""
    root = Path(root_dir)
    week_dirs = sorted((root / "x-weekly").glob("*-x-week-*"))
    tweets: list[dict[str, Any]] = []
    for week_dir in week_dirs:
        article_path = week_dir / "article.md"
        if not article_path.is_file():
            continue
        tweets.extend(parse_weekly_article(article_path, week_dir.name))
    tweets.sort(key=lambda tweet: tweet["created_at"])
    return tweets


def parse_weekly_article(article_path: str | Path, week_key: str) -> list[dict[str, Any]]:
    path = Path(article_path)
    year = int(week_key[:4])
    current_month = 1
    current_day = 1
    pending_refs: list[str] = []
    parsed: list[dict[str, Any]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    index = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        day_match = DAY_RE.match(line)
        if day_match:
            current_month = int(day_match.group(1))
            current_day = int(day_match.group(2))
            pending_refs = []
            i += 1
            continue
        if line.startswith(">"):
            pending_refs.append(line)
            i += 1
            continue
        time_match = TIME_RE.match(line)
        if not time_match:
            i += 1
            continue

        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        text_lines = [time_match.group(3)]
        metrics = {"reply_count": 0, "like_count": 0, "retweet_count": 0}
        i += 1
        while i < len(lines):
            next_line = lines[i]
            if next_line.startswith("<small>"):
                metrics = parse_metrics(next_line)
                i += 1
                break
            if next_line.startswith("## ") or next_line.startswith(">") or TIME_RE.match(next_line):
                break
            text_lines.append(next_line)
            i += 1

        is_reply_entry = any("↩️ 回复" in ref for ref in pending_refs)
        is_quote_entry = any("🔁 引用" in ref for ref in pending_refs)
        if not is_reply_entry:
            index += 1
            text = "\n".join(text_lines).strip()
            tweet_id = f"{week_key}:{index:03d}"
            parsed.append({
                "id": tweet_id,
                "created_at": f"{year:04d}-{current_month:02d}-{current_day:02d}T{hour:02d}:{minute:02d}:00",
                "text": text,
                "url": "",
                "metrics": metrics,
                "kind": "quote" if is_quote_entry else "tweet",
            })
        pending_refs = []
    return parsed


def build_openai_payload(model: str, prompt: str, tweets: list[dict[str, Any]]) -> dict[str, Any]:
    source = [{"id": str(tweet["id"]), "text": tweet["text"]} for tweet in tweets]
    instructions = (
        "You rewrite X posts. Preserve each post's meaning, rewrite every tweet "
        "independently, keep the same IDs, keep the same order, and return valid JSON "
        "only in this exact shape: {\"versions\":[{\"id\":\"...\",\"text\":\"...\"}]}."
    )
    input_text = (
        "Rewrite every tweet using this prompt:\n"
        f"{prompt}\n\n"
        "Tweets JSON:\n"
        f"{json.dumps(source, ensure_ascii=False, indent=2)}"
    )
    return {"model": model, "instructions": instructions, "input": input_text}


def extract_response_text(payload: dict[str, Any]) -> str:
    text = payload.get("output_text")
    if isinstance(text, str) and text.strip():
        return text
    chunks: list[str] = []
    for item in payload.get("output") or []:
        for content in item.get("content") or []:
            if isinstance(content.get("text"), str):
                chunks.append(content["text"])
    if chunks:
        return "\n".join(chunks)
    raise PlaygroundError("OpenAI response did not include output text")


def parse_rewrite_response(text: str, tweet_ids: list[str]) -> list[dict[str, str]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PlaygroundError(f"OpenAI returned invalid JSON: {exc}") from exc

    versions = payload.get("versions")
    if not isinstance(versions, list):
        raise PlaygroundError("OpenAI JSON must contain versions[]")

    by_id: dict[str, str] = {}
    for item in versions:
        if not isinstance(item, dict):
            raise PlaygroundError("Each version must be an object")
        tweet_id = str(item.get("id", ""))
        rewritten = item.get("text")
        if not tweet_id or not isinstance(rewritten, str):
            raise PlaygroundError("Each version must contain id and text")
        by_id[tweet_id] = rewritten

    missing = [tweet_id for tweet_id in tweet_ids if tweet_id not in by_id]
    if missing:
        raise PlaygroundError(f"OpenAI response missed tweet IDs: {', '.join(missing[:5])}")

    return [{"id": tweet_id, "text": by_id[tweet_id]} for tweet_id in tweet_ids]


def rewrite_with_openai(
    prompt: str,
    tweets: list[dict[str, Any]],
    api_key: str,
    model: str,
) -> list[dict[str, str]]:
    body = json.dumps(build_openai_payload(model, prompt, tweets), ensure_ascii=False).encode("utf-8")
    req = request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # urllib raises several concrete types; keep message user-facing.
        raise PlaygroundError(f"OpenAI request failed: {exc}") from exc
    return parse_rewrite_response(extract_response_text(payload), [str(tweet["id"]) for tweet in tweets])


def load_env_file(env_path: str | Path) -> None:
    path = Path(env_path).expanduser()
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class PlaygroundHandler(SimpleHTTPRequestHandler):
    root_dir = Path.cwd()
    static_dir = Path.cwd() / "playground"
    tweets_cache: list[dict[str, Any]] | None = None

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def json_error(self, status: int, message: str) -> None:
        self.send_json(status, {"error": message})

    def do_GET(self) -> None:
        if self.path == "/":
            self.send_response(302)
            self.send_header("Location", "/index.html")
            self.end_headers()
            return
        if self.path == "/api/tweets":
            try:
                tweets = self.get_tweets()
                self.send_json(200, {"tweets": tweets})
            except PlaygroundError as exc:
                self.json_error(500, str(exc))
            return
        self.serve_static()

    def do_POST(self) -> None:
        if self.path != "/api/rewrite":
            self.json_error(404, "Not found")
            return
        try:
            body = self.read_json_body()
            prompt = str(body.get("prompt", "")).strip()
            tweet_ids = [str(tweet_id) for tweet_id in body.get("tweet_ids") or []]
            if not prompt:
                raise PlaygroundError("Prompt is required")
            api_key = os.environ.get("OPENAI_API_KEY", "").strip()
            model = os.environ.get("OPENAI_MODEL", "gpt-4.1").strip()
            if not api_key:
                raise PlaygroundError("OPENAI_API_KEY is not set")
            tweets_by_id = {tweet["id"]: tweet for tweet in self.get_tweets()}
            selected = [tweets_by_id[tweet_id] for tweet_id in tweet_ids if tweet_id in tweets_by_id]
            if len(selected) != len(tweet_ids):
                raise PlaygroundError("Request included unknown tweet IDs")
            versions = rewrite_with_openai(prompt, selected, api_key, model)
            self.send_json(200, {"prompt": prompt, "versions": versions})
        except PlaygroundError as exc:
            self.json_error(500, str(exc))
        except Exception as exc:
            self.json_error(500, f"Unexpected server error: {exc}")

    def get_tweets(self) -> list[dict[str, Any]]:
        if self.__class__.tweets_cache is None:
            self.__class__.tweets_cache = load_latest_tweets(self.__class__.root_dir)
        return self.__class__.tweets_cache

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PlaygroundError(f"Invalid JSON body: {exc}") from exc
        if not isinstance(payload, dict):
            raise PlaygroundError("JSON body must be an object")
        return payload

    def serve_static(self) -> None:
        rel_path = self.path.split("?", 1)[0].lstrip("/")
        target = (self.__class__.static_dir / rel_path).resolve()
        static_root = self.__class__.static_dir.resolve()
        if not str(target).startswith(str(static_root)) or not target.is_file():
            self.send_error(404)
            return
        data = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the X tweet rewrite playground")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--root", default=os.getcwd())
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    load_env_file(root.parent / ".env")
    load_env_file(Path.home() / "code" / ".env")
    PlaygroundHandler.root_dir = root
    PlaygroundHandler.static_dir = root / "playground"
    PlaygroundHandler.tweets_cache = None

    server = ThreadingHTTPServer((args.host, args.port), PlaygroundHandler)
    print(f"http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
