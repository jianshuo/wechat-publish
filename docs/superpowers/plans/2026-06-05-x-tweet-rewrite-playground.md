# X Tweet Rewrite Playground Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local browser playground that loads non-reply tweets from `x-weekly`, rewrites all tweets with a user prompt through OpenAI, and compares many prompt runs side by side.

**Architecture:** Add one dependency-free Python HTTP server in `tools/x_tweet_playground.py`. It loads the latest `x-weekly/.cache/tweets-*.json`, exposes JSON APIs, serves static files from `playground/`, and calls OpenAI's Responses API using `urllib.request`. The UI is plain HTML/CSS/JS and keeps prompt comparisons in memory.

**Tech Stack:** Python standard library `http.server`, `json`, `urllib.request`; framework-free browser JavaScript; existing `unittest` test style.

---

### Task 1: Server Data Functions

**Files:**
- Create: `tools/x_tweet_playground.py`
- Create: `tools/tests/test_x_tweet_playground.py`

- [ ] **Step 1: Write failing tests for cache selection and tweet filtering**

Create `tools/tests/test_x_tweet_playground.py` with tests that build temporary cache files, call `latest_cache_file`, `load_tweets_from_cache`, and assert replies are removed while quote tweets remain.

- [ ] **Step 2: Run tests to verify failure**

Run: `python3 -m unittest tools.tests.test_x_tweet_playground -v`

Expected: FAIL because `x_tweet_playground` does not exist.

- [ ] **Step 3: Implement data helpers**

Create `tools/x_tweet_playground.py` with:

- `latest_cache_file(cache_dir)`
- `tweet_url(tweet_id)`
- `class PlaygroundError(RuntimeError)`
- `normalize_tweet(tweet)`
- `is_reply(tweet)`
- `load_tweets_from_cache(cache_path)`
- `load_latest_tweets(root_dir)`

The helpers must sort tweets by `created_at`, exclude replies via `referenced_tweets.type == "replied_to"` or `in_reply_to_user_id`, keep quote tweets, and return compact dictionaries with `id`, `created_at`, `text`, `url`, `metrics`, and `kind`.

- [ ] **Step 4: Run tests to verify pass**

Run: `python3 -m unittest tools.tests.test_x_tweet_playground -v`

Expected: PASS.

### Task 2: OpenAI Rewrite Client

**Files:**
- Modify: `tools/x_tweet_playground.py`
- Modify: `tools/tests/test_x_tweet_playground.py`

- [ ] **Step 1: Add tests for rewrite JSON parsing and prompt payload**

Add tests for:

- `parse_rewrite_response` accepts JSON with `versions: [{id, text}]`.
- It rejects missing IDs.
- `build_openai_payload` includes model, instructions, and tweet IDs.

- [ ] **Step 2: Run tests to verify failure**

Run: `python3 -m unittest tools.tests.test_x_tweet_playground -v`

Expected: FAIL because the OpenAI helpers are not implemented.

- [ ] **Step 3: Implement rewrite helpers**

Add:

- `build_openai_payload(model, prompt, tweets)`
- `extract_response_text(payload)`
- `parse_rewrite_response(text, tweet_ids)`
- `rewrite_with_openai(prompt, tweets, api_key, model)`

Use `POST https://api.openai.com/v1/responses` with JSON body containing `model`, `instructions`, and `input`. Parse `output_text` first, then fall back to `output[].content[].text`.

- [ ] **Step 4: Run tests to verify pass**

Run: `python3 -m unittest tools.tests.test_x_tweet_playground -v`

Expected: PASS.

### Task 3: HTTP Server

**Files:**
- Modify: `tools/x_tweet_playground.py`

- [ ] **Step 1: Add request handler**

Implement a `PlaygroundHandler` with:

- `GET /` redirecting to `/index.html`
- `GET /api/tweets` returning `{tweets}`
- `POST /api/rewrite` reading `{prompt, tweet_ids}` and returning `{prompt, versions}`
- Static file serving from `playground/`

Reject missing `OPENAI_API_KEY` or `OPENAI_MODEL` with HTTP 500 JSON errors.

- [ ] **Step 2: Add CLI entrypoint**

Add `main(argv=None)` accepting `--host`, `--port`, and `--root`, then run `ThreadingHTTPServer`.

- [ ] **Step 3: Smoke-test server import**

Run: `python3 -m py_compile tools/x_tweet_playground.py`

Expected: no output and exit 0.

### Task 4: Browser UI

**Files:**
- Create: `playground/index.html`
- Create: `playground/styles.css`
- Create: `playground/app.js`

- [ ] **Step 1: Create HTML shell**

Create the top prompt bar, fixed original column, and horizontally scrollable versions area.

- [ ] **Step 2: Create CSS**

Use a restrained tool UI: compact typography, stable row sizing, table-like aligned rows, no card-in-card nesting, responsive behavior for narrower screens.

- [ ] **Step 3: Create JS behavior**

Implement:

- Load tweets from `/api/tweets`.
- Render original rows.
- On prompt submit, append a version column with loading state.
- POST `/api/rewrite` with `{prompt, tweet_ids}`.
- Align returned rewrites by tweet ID.
- Show API errors in the version column.

### Task 5: Verification

**Files:**
- Modify as needed only for defects found during verification.

- [ ] **Step 1: Run unit tests**

Run: `python3 -m unittest tools.tests.test_x_tweet_playground -v`

Expected: PASS.

- [ ] **Step 2: Run existing weekly archive tests**

Run: `python3 -m unittest tools.tests.test_x_weekly_archive -v`

Expected: PASS.

- [ ] **Step 3: Start server**

Run: `python3 tools/x_tweet_playground.py --port 8765`

Expected: server starts and prints `http://127.0.0.1:8765/`.

- [ ] **Step 4: Browser verification**

Open `http://127.0.0.1:8765/`, confirm original non-reply tweets load, submit a prompt, and confirm either rewrites appear or a clear missing-configuration error appears.

