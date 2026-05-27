# wjs-syndicating-articles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `wjs-syndicating-articles` Claude Code skill that, on a daily schedule, picks the newest un-syndicated 公众号 article, extracts one core copy, auto-posts to API platforms (X / Bluesky / Threads / LinkedIn), prepares an outbox for manual platforms (Facebook / 小红书 / 即刻), and notifies the user.

**Architecture:** A `SKILL.md` orchestrator (Claude-executed) drives a set of small, independently-testable bash scripts. Each platform poster is isolated (`try/catch` at the orchestrator level) and idempotent via `state/history.jsonl` keyed on `(slug, platform)`. Missing API credentials degrade a platform to the outbox instead of failing the run. Copy extraction is a Claude reasoning step (reads `article.md`, writes `post.txt`); everything mechanical (pick / post / outbox / history / dedup) is a tested bash script.

**Tech Stack:** Bash, `jq` (1.7, installed), `xurl` (installed, X auth ready), `curl` (Bluesky/Threads/LinkedIn REST), macOS `pbcopy`/`open` for the interactive `--open` mode, plain-bash test harness (no test framework dependency).

**Skill install location:** `~/.claude/skills/wjs-syndicating-articles/` (outside this repo, like the sibling `wjs-tweeting-from-articles`). All paths below are relative to that dir unless absolute.

---

## File Structure

```
~/.claude/skills/wjs-syndicating-articles/
├── SKILL.md                    # orchestrator instructions (Task 9)
├── config.json                 # enabled platforms + modes + schedule (Task 1)
├── secrets.json.example        # credential template, real one gitignored (Task 1)
├── .gitignore                  # secrets.json, state/, outbox/ (Task 1)
├── scripts/
│   ├── lib.sh                  # shared: SKILL_DIR, jq guards, config/secret readers (Task 2)
│   ├── history.sh              # record / has / fully-done (Task 3)
│   ├── pick-next-article.sh    # newest not-fully-syndicated folder (Task 4)
│   ├── post-x.sh               # xurl POST (Task 5)
│   ├── post-bluesky.sh         # atproto session + createRecord (Task 6)
│   ├── post-threads.sh         # Threads container + publish (Task 7)
│   ├── post-linkedin.sh        # /v2/ugcPosts (Task 8)
│   ├── build-outbox.sh         # post.txt + image.png + OPEN.md (Task 9 pre-req, built Task 8.5)
│   └── test/
│       ├── assert.sh           # tiny assert helpers (Task 1)
│       ├── fixtures/           # fake articles dir + secrets (created per-test)
│       ├── test_history.sh     # (Task 3)
│       ├── test_pick.sh        # (Task 4)
│       ├── test_post_x.sh      # (Task 5)
│       ├── test_post_bluesky.sh# (Task 6)
│       ├── test_post_threads.sh# (Task 7)
│       ├── test_post_linkedin.sh#(Task 8)
│       ├── test_build_outbox.sh# (Task 8.5)
│       └── test_e2e_dryrun.sh  # end-to-end dry-run smoke (Task 10)
├── outbox/<date>-<slug>/       # runtime output (gitignored)
└── state/history.jsonl         # runtime state (gitignored)
```

**Exit-code contract for all `post-*.sh` scripts** (so the orchestrator can branch uniformly):
- `0` — posted successfully (stdout contains `url=...` and optionally `post_id=...`)
- `3` — credentials missing/incomplete → orchestrator records `queued` with `reason:"no_creds"` and adds platform to outbox
- any other non-zero — attempt failed → orchestrator records `failed` (retried next run)

---

### Task 1: Scaffold skill dir, config, gitignore, assert helper

**Files:**
- Create: `~/.claude/skills/wjs-syndicating-articles/config.json`
- Create: `~/.claude/skills/wjs-syndicating-articles/secrets.json.example`
- Create: `~/.claude/skills/wjs-syndicating-articles/.gitignore`
- Create: `~/.claude/skills/wjs-syndicating-articles/scripts/test/assert.sh`

- [ ] **Step 1: Create directories**

Run:
```bash
mkdir -p ~/.claude/skills/wjs-syndicating-articles/scripts/test/fixtures
```

- [ ] **Step 2: Write `config.json`**

```json
{
  "articles_dir": "/Users/jianshuo/code/wechat-publish/articles",
  "author": "王建硕",
  "article_url_base": "https://mp.weixin.qq.com/",
  "schedule": "10:00",
  "platforms": {
    "x":           { "mode": "api" },
    "bluesky":     { "mode": "api" },
    "threads":     { "mode": "api" },
    "linkedin":    { "mode": "api" },
    "facebook":    { "mode": "outbox", "web_compose": "https://www.facebook.com/" },
    "xiaohongshu": { "mode": "outbox", "web_compose": "https://creator.xiaohongshu.com/publish/publish" },
    "jike":        { "mode": "outbox", "web_compose": "https://web.okjike.com/" },
    "zhihu":       { "mode": "outbox", "web_compose": "https://zhuanlan.zhihu.com/write" }
  }
}
```

- [ ] **Step 3: Write `secrets.json.example`**

```json
{
  "bluesky":  { "handle": "you.bsky.social", "app_password": "xxxx-xxxx-xxxx-xxxx" },
  "threads":  { "access_token": "THREADS_LONG_LIVED_TOKEN", "user_id": "1784..." },
  "linkedin": { "access_token": "LINKEDIN_TOKEN", "author_urn": "urn:li:person:abc123" }
}
```

- [ ] **Step 4: Write `.gitignore`**

```
secrets.json
state/
outbox/
scripts/test/fixtures/
```

- [ ] **Step 5: Write `scripts/test/assert.sh`**

```bash
#!/usr/bin/env bash
# Tiny assert helpers. Source this in test scripts.
ASSERT_FAILS=0
assert_eq() { # actual expected msg
  if [[ "$1" == "$2" ]]; then echo "  ok: $3"
  else echo "  FAIL: $3"; echo "    expected: [$2]"; echo "    actual:   [$1]"; ASSERT_FAILS=$((ASSERT_FAILS+1)); fi
}
assert_contains() { # haystack needle msg
  if [[ "$1" == *"$2"* ]]; then echo "  ok: $3"
  else echo "  FAIL: $3"; echo "    [$1] does not contain [$2]"; ASSERT_FAILS=$((ASSERT_FAILS+1)); fi
}
assert_exit() { # actual_code expected_code msg
  if [[ "$1" == "$2" ]]; then echo "  ok: $3"
  else echo "  FAIL: $3 (exit $1, wanted $2)"; ASSERT_FAILS=$((ASSERT_FAILS+1)); fi
}
assert_file() { # path msg
  if [[ -f "$1" ]]; then echo "  ok: $2"
  else echo "  FAIL: $2 (no file $1)"; ASSERT_FAILS=$((ASSERT_FAILS+1)); fi
}
finish() { # name
  if [[ "$ASSERT_FAILS" -eq 0 ]]; then echo "PASS: $1"; exit 0
  else echo "FAILED: $1 ($ASSERT_FAILS assertions)"; exit 1; fi
}
```

- [ ] **Step 6: Commit**

This skill dir is not a git repo by default. Initialize one so the plan's commit steps work and secrets stay ignored:
```bash
cd ~/.claude/skills/wjs-syndicating-articles
git init -q 2>/dev/null || true
git add config.json secrets.json.example .gitignore scripts/test/assert.sh
git commit -q -m "scaffold: config, gitignore, assert helper" || true
```

---

### Task 2: Shared lib (`lib.sh`)

**Files:**
- Create: `scripts/lib.sh`

- [ ] **Step 1: Write `scripts/lib.sh`**

```bash
#!/usr/bin/env bash
# Shared helpers. Source with:  source "$(dirname "$0")/lib.sh"
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="${SYND_CONFIG:-$SKILL_DIR/config.json}"
SECRETS="${SYND_SECRETS:-$SKILL_DIR/secrets.json}"
HISTORY="${SYND_HISTORY:-$SKILL_DIR/state/history.jsonl}"

command -v jq >/dev/null  || { echo "jq not installed" >&2; exit 1; }

cfg()  { jq -r "$1" "$CONFIG"; }                         # cfg '.articles_dir'
secret() {                                               # secret '.bluesky.handle' -> value or empty
  [[ -f "$SECRETS" ]] || { echo ""; return 0; }
  jq -r "$1 // empty" "$SECRETS" 2>/dev/null || echo ""
}
enabled_platforms() { jq -r '.platforms | keys[]' "$CONFIG"; }
platform_mode() { jq -r --arg p "$1" '.platforms[$p].mode' "$CONFIG"; }
ensure_state() { mkdir -p "$(dirname "$HISTORY")"; touch "$HISTORY"; }
```

- [ ] **Step 2: Smoke-test it reads config**

Run:
```bash
cd ~/.claude/skills/wjs-syndicating-articles
bash -c 'source scripts/lib.sh; cfg ".author"; enabled_platforms | tr "\n" " "; echo'
```
Expected: prints `王建硕` then `x bluesky threads linkedin facebook xiaohongshu jike`

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills/wjs-syndicating-articles
git add scripts/lib.sh && git commit -q -m "feat: shared lib.sh (config/secret readers)"
```

---

### Task 3: `history.sh` (record / has / fully-done) — TDD

**Files:**
- Create: `scripts/history.sh`
- Test: `scripts/test/test_history.sh`

- [ ] **Step 1: Write the failing test `scripts/test/test_history.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/assert.sh"
SKILL="$(cd "$HERE/../.." && pwd)"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export SYND_CONFIG="$SKILL/config.json"
export SYND_HISTORY="$TMP/history.jsonl"

H="$SKILL/scripts/history.sh"

# initially nothing recorded -> has returns 1
bash "$H" has slugA x; assert_exit $? 1 "has on empty history -> 1"

# record a posted X -> has returns 0
bash "$H" record slugA x posted "https://x.com/u/1" "1"
bash "$H" has slugA x; assert_exit $? 0 "has after posted -> 0"

# queued counts as done
bash "$H" record slugA facebook queued "" "" no_creds
bash "$H" has slugA facebook; assert_exit $? 0 "has after queued -> 0"

# failed does NOT count as done (retry)
bash "$H" record slugA bluesky failed
bash "$H" has slugA bluesky; assert_exit $? 1 "has after failed -> 1 (retry)"

# fully-done: slugA not done until ALL enabled platforms done
bash "$H" fully-done slugA; assert_exit $? 1 "fully-done false while some platforms missing"

# record done for every enabled platform
for p in x bluesky threads linkedin facebook xiaohongshu jike zhihu; do
  bash "$H" record slugA "$p" queued
done
bash "$H" fully-done slugA; assert_exit $? 0 "fully-done true after all platforms done"

# the recorded line is valid JSON with expected fields
LINE="$(grep '"platform":"x"' "$SYND_HISTORY" | head -1)"
assert_eq "$(echo "$LINE" | jq -r .status)" "posted" "x record status posted"
assert_eq "$(echo "$LINE" | jq -r .url)" "https://x.com/u/1" "x record url"

finish test_history
```

- [ ] **Step 2: Run to verify it fails**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_history.sh
```
Expected: FAIL (history.sh does not exist / command errors)

- [ ] **Step 3: Write `scripts/history.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
ensure_state

cmd="${1:-}"; shift || true

case "$cmd" in
  record)  # record <slug> <platform> <status> [url] [post_id] [reason]
    slug="$1"; platform="$2"; status="$3"; url="${4:-}"; post_id="${5:-}"; reason="${6:-}"
    jq -nc --arg date "$(date +%F)" --arg slug "$slug" --arg platform "$platform" \
           --arg status "$status" --arg url "$url" --arg post_id "$post_id" --arg reason "$reason" \
       '{date:$date,slug:$slug,platform:$platform,status:$status}
        + (if $url != "" then {url:$url} else {} end)
        + (if $post_id != "" then {post_id:$post_id} else {} end)
        + (if $reason != "" then {reason:$reason} else {} end)' >> "$HISTORY"
    ;;
  has)     # has <slug> <platform>  -> exit 0 if done (posted|queued|skipped)
    slug="$1"; platform="$2"
    if jq -e --arg s "$slug" --arg p "$platform" \
        'select(.slug==$s and .platform==$p and (.status=="posted" or .status=="queued" or .status=="skipped"))' \
        "$HISTORY" >/dev/null 2>&1; then exit 0; else exit 1; fi
    ;;
  fully-done)  # fully-done <slug> -> exit 0 if every enabled platform is done
    slug="$1"
    for p in $(enabled_platforms); do
      if ! "$0" has "$slug" "$p"; then exit 1; fi
    done
    exit 0
    ;;
  *) echo "usage: history.sh {record|has|fully-done} ..." >&2; exit 2 ;;
esac
```

- [ ] **Step 4: Run to verify it passes**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_history.sh
```
Expected: `PASS: test_history`

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/wjs-syndicating-articles
git add scripts/history.sh scripts/test/test_history.sh
git commit -q -m "feat: history.sh with dedup (record/has/fully-done) + tests"
```

---

### Task 4: `pick-next-article.sh` — TDD

**Files:**
- Create: `scripts/pick-next-article.sh`
- Test: `scripts/test/test_pick.sh`

- [ ] **Step 1: Write the failing test `scripts/test/test_pick.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/assert.sh"
SKILL="$(cd "$HERE/../.." && pwd)"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ART="$TMP/articles"; mkdir -p "$ART/2026-05-10-aaa" "$ART/2026-05-12-ccc" "$ART/2026-05-11-bbb"
# write a fake config pointing at the temp articles dir
CFG="$TMP/config.json"
jq --arg dir "$ART" '.articles_dir=$dir' "$SKILL/config.json" > "$CFG"
export SYND_CONFIG="$CFG"
export SYND_HISTORY="$TMP/history.jsonl"; : > "$SYND_HISTORY"

PICK="$SKILL/scripts/pick-next-article.sh"

# nothing syndicated -> newest folder (ccc, 05-12) is picked
OUT="$(bash "$PICK")"
assert_eq "$(basename "$OUT")" "2026-05-12-ccc" "picks newest by date desc"

# mark ccc fully done -> next newest (bbb, 05-11)
for p in x bluesky threads linkedin facebook xiaohongshu jike zhihu; do
  bash "$SKILL/scripts/history.sh" record 2026-05-12-ccc "$p" posted
done
OUT="$(bash "$PICK")"
assert_eq "$(basename "$OUT")" "2026-05-11-bbb" "skips fully-done, picks next newest"

# mark all done -> empty output, exit 0 (rest day)
for s in 2026-05-11-bbb 2026-05-10-aaa; do
  for p in x bluesky threads linkedin facebook xiaohongshu jike zhihu; do
    bash "$SKILL/scripts/history.sh" record "$s" "$p" posted
  done
done
OUT="$(bash "$PICK")"; CODE=$?
assert_eq "$OUT" "" "all done -> empty output"
assert_exit "$CODE" 0 "all done -> exit 0 (rest day)"

finish test_pick
```

- [ ] **Step 2: Run to verify it fails**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_pick.sh
```
Expected: FAIL (pick-next-article.sh missing)

- [ ] **Step 3: Write `scripts/pick-next-article.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
ensure_state
HIST_SH="$(dirname "${BASH_SOURCE[0]}")/history.sh"

ART_DIR="$(cfg '.articles_dir')"
[[ -d "$ART_DIR" ]] || { echo "articles_dir not found: $ART_DIR" >&2; exit 1; }

# folders named like 20YY-MM-DD-slug, newest date first
while IFS= read -r dir; do
  [[ -d "$dir" ]] || continue
  slug="$(basename "$dir")"
  if ! bash "$HIST_SH" fully-done "$slug"; then
    echo "$dir"; exit 0
  fi
done < <(find "$ART_DIR" -maxdepth 1 -type d -name '20*-*' | sort -r)

# none left -> rest day
exit 0
```

- [ ] **Step 4: Run to verify it passes**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_pick.sh
```
Expected: `PASS: test_pick`

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/wjs-syndicating-articles
git add scripts/pick-next-article.sh scripts/test/test_pick.sh
git commit -q -m "feat: pick-next-article.sh (newest not-fully-syndicated) + tests"
```

---

### Task 5: `post-x.sh` — TDD (dry-run + payload shape)

**Files:**
- Create: `scripts/post-x.sh`
- Test: `scripts/test/test_post_x.sh`

> X always has credentials via `xurl`, so there is no `no_creds` path here. We test the dry-run payload (no network). Live posting is verified manually in Task 11.

- [ ] **Step 1: Write the failing test `scripts/test/test_post_x.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/assert.sh"
SKILL="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

POST_TXT="$TMP/post.txt"; printf '手感这东西，得每天练。\nhttps://mp.weixin.qq.com/x' > "$POST_TXT"

OUT="$(bash "$SKILL/scripts/post-x.sh" "$POST_TXT" --dry-run)"; CODE=$?
assert_exit "$CODE" 0 "dry-run exits 0"
assert_contains "$OUT" '"text"' "dry-run prints JSON payload with text field"
assert_contains "$OUT" "手感这东西" "dry-run payload contains the copy"

finish test_post_x
```

- [ ] **Step 2: Run to verify it fails**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_post_x.sh
```
Expected: FAIL (post-x.sh missing)

- [ ] **Step 3: Write `scripts/post-x.sh`**

```bash
#!/usr/bin/env bash
# post-x.sh <post.txt> [--dry-run]   exit: 0 ok / non-zero fail
set -uo pipefail
TXT_FILE="${1:?usage: post-x.sh <post.txt> [--dry-run]}"
DRY="${2:-}"
TEXT="$(cat "$TXT_FILE")"
JSON="$(jq -nc --arg text "$TEXT" '{text:$text}')"

if [[ "$DRY" == "--dry-run" ]]; then echo "$JSON"; exit 0; fi

resp="$(xurl -X POST -d "$JSON" /2/tweets)" || { echo "xurl failed: $resp" >&2; exit 1; }
# X echoes raw newlines in `text`; grep id directly (strict jq would choke).
id="$(printf '%s' "$resp" | grep -oE '"id":"[0-9]+"' | head -1 | sed -E 's/.*"([0-9]+)".*/\1/')"
[[ -n "$id" ]] || { echo "no tweet id: $resp" >&2; exit 1; }
echo "url=https://x.com/jianshuo/status/$id"
echo "post_id=$id"
```

- [ ] **Step 4: Run to verify it passes**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_post_x.sh
```
Expected: `PASS: test_post_x`

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/wjs-syndicating-articles
git add scripts/post-x.sh scripts/test/test_post_x.sh
git commit -q -m "feat: post-x.sh (xurl) + dry-run test"
```

---

### Task 6: `post-bluesky.sh` — TDD (no-creds degrade + dry-run)

**Files:**
- Create: `scripts/post-bluesky.sh`
- Test: `scripts/test/test_post_bluesky.sh`

- [ ] **Step 1: Write the failing test `scripts/test/test_post_bluesky.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/assert.sh"
SKILL="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

POST_TXT="$TMP/post.txt"; printf '手感这东西，得每天练。' > "$POST_TXT"

# no secrets file -> exit 3 (degrade)
export SYND_SECRETS="$TMP/none.json"
bash "$SKILL/scripts/post-bluesky.sh" "$POST_TXT"; assert_exit $? 3 "missing secrets -> exit 3"

# secrets present but dry-run -> exit 0, no network
echo '{"bluesky":{"handle":"me.bsky.social","app_password":"abcd"}}' > "$TMP/sec.json"
export SYND_SECRETS="$TMP/sec.json"
OUT="$(bash "$SKILL/scripts/post-bluesky.sh" "$POST_TXT" --dry-run)"; CODE=$?
assert_exit "$CODE" 0 "dry-run with creds -> exit 0"
assert_contains "$OUT" "手感这东西" "dry-run echoes the text"

# secrets file present but incomplete (no app_password) -> exit 3
echo '{"bluesky":{"handle":"me.bsky.social"}}' > "$TMP/partial.json"
export SYND_SECRETS="$TMP/partial.json"
bash "$SKILL/scripts/post-bluesky.sh" "$POST_TXT"; assert_exit $? 3 "incomplete creds -> exit 3"

finish test_post_bluesky
```

- [ ] **Step 2: Run to verify it fails**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_post_bluesky.sh
```
Expected: FAIL (post-bluesky.sh missing)

- [ ] **Step 3: Write `scripts/post-bluesky.sh`**

```bash
#!/usr/bin/env bash
# post-bluesky.sh <post.txt> [--dry-run]  exit: 0 ok / 3 no creds / other fail
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
TXT_FILE="${1:?usage: post-bluesky.sh <post.txt> [--dry-run]}"
DRY="${2:-}"
TEXT="$(cat "$TXT_FILE")"

HANDLE="$(secret '.bluesky.handle')"
APPPW="$(secret '.bluesky.app_password')"
[[ -n "$HANDLE" && -n "$APPPW" ]] || { echo "bluesky: no creds" >&2; exit 3; }

if [[ "$DRY" == "--dry-run" ]]; then echo "bluesky would post: $TEXT"; exit 0; fi

PDS="https://bsky.social"
sess="$(curl -fsS -X POST "$PDS/xrpc/com.atproto.server.createSession" \
  -H 'Content-Type: application/json' \
  -d "$(jq -nc --arg id "$HANDLE" --arg pw "$APPPW" '{identifier:$id,password:$pw}')")" \
  || { echo "bluesky session failed" >&2; exit 1; }
JWT="$(echo "$sess" | jq -r .accessJwt)"; DID="$(echo "$sess" | jq -r .did)"
[[ -n "$JWT" && "$JWT" != "null" ]] || { echo "bluesky auth failed: $sess" >&2; exit 1; }

NOW="$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
rec="$(jq -nc --arg t "$TEXT" --arg now "$NOW" --arg did "$DID" \
  '{repo:$did,collection:"app.bsky.feed.post",record:{ "$type":"app.bsky.feed.post", text:$t, createdAt:$now }}')"
resp="$(curl -fsS -X POST "$PDS/xrpc/com.atproto.repo.createRecord" \
  -H "Authorization: Bearer $JWT" -H 'Content-Type: application/json' -d "$rec")" \
  || { echo "bluesky post failed: $resp" >&2; exit 1; }
uri="$(echo "$resp" | jq -r .uri)"
rkey="${uri##*/}"
echo "url=https://bsky.app/profile/$HANDLE/post/$rkey"
echo "post_id=$rkey"
```

- [ ] **Step 4: Run to verify it passes**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_post_bluesky.sh
```
Expected: `PASS: test_post_bluesky`

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/wjs-syndicating-articles
git add scripts/post-bluesky.sh scripts/test/test_post_bluesky.sh
git commit -q -m "feat: post-bluesky.sh (atproto) + degrade/dry-run tests"
```

---

### Task 7: `post-threads.sh` — TDD (no-creds degrade + dry-run)

**Files:**
- Create: `scripts/post-threads.sh`
- Test: `scripts/test/test_post_threads.sh`

> Threads API is two calls: create a text media container, then publish it. We test only the degrade + dry-run paths (no network).

- [ ] **Step 1: Write the failing test `scripts/test/test_post_threads.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/assert.sh"
SKILL="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
POST_TXT="$TMP/post.txt"; printf '少跟 AI 聊天，多写程序。' > "$POST_TXT"

export SYND_SECRETS="$TMP/none.json"
bash "$SKILL/scripts/post-threads.sh" "$POST_TXT"; assert_exit $? 3 "missing creds -> exit 3"

echo '{"threads":{"access_token":"tok","user_id":"123"}}' > "$TMP/sec.json"
export SYND_SECRETS="$TMP/sec.json"
OUT="$(bash "$SKILL/scripts/post-threads.sh" "$POST_TXT" --dry-run)"; CODE=$?
assert_exit "$CODE" 0 "dry-run with creds -> exit 0"
assert_contains "$OUT" "少跟 AI 聊天" "dry-run echoes the text"

finish test_post_threads
```

- [ ] **Step 2: Run to verify it fails**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_post_threads.sh
```
Expected: FAIL (post-threads.sh missing)

- [ ] **Step 3: Write `scripts/post-threads.sh`**

```bash
#!/usr/bin/env bash
# post-threads.sh <post.txt> [--dry-run]  exit: 0 ok / 3 no creds / other fail
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
TXT_FILE="${1:?usage: post-threads.sh <post.txt> [--dry-run]}"
DRY="${2:-}"
TEXT="$(cat "$TXT_FILE")"

TOKEN="$(secret '.threads.access_token')"
UID_="$(secret '.threads.user_id')"
[[ -n "$TOKEN" && -n "$UID_" ]] || { echo "threads: no creds" >&2; exit 3; }

if [[ "$DRY" == "--dry-run" ]]; then echo "threads would post: $TEXT"; exit 0; fi

API="https://graph.threads.net/v1.0"
# 1) create container
cre="$(curl -fsS -X POST "$API/$UID_/threads" \
  --data-urlencode "media_type=TEXT" \
  --data-urlencode "text=$TEXT" \
  --data-urlencode "access_token=$TOKEN")" || { echo "threads container failed: $cre" >&2; exit 1; }
CID="$(echo "$cre" | jq -r .id)"
[[ -n "$CID" && "$CID" != "null" ]] || { echo "threads no container id: $cre" >&2; exit 1; }
# 2) publish
pub="$(curl -fsS -X POST "$API/$UID_/threads_publish" \
  --data-urlencode "creation_id=$CID" \
  --data-urlencode "access_token=$TOKEN")" || { echo "threads publish failed: $pub" >&2; exit 1; }
PID="$(echo "$pub" | jq -r .id)"
[[ -n "$PID" && "$PID" != "null" ]] || { echo "threads no post id: $pub" >&2; exit 1; }
echo "url=https://www.threads.net/@$(secret '.threads.username' || echo me)/post/$PID"
echo "post_id=$PID"
```

- [ ] **Step 4: Run to verify it passes**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_post_threads.sh
```
Expected: `PASS: test_post_threads`

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/wjs-syndicating-articles
git add scripts/post-threads.sh scripts/test/test_post_threads.sh
git commit -q -m "feat: post-threads.sh (Threads API) + degrade/dry-run tests"
```

---

### Task 8: `post-linkedin.sh` — TDD (no-creds degrade + dry-run)

**Files:**
- Create: `scripts/post-linkedin.sh`
- Test: `scripts/test/test_post_linkedin.sh`

- [ ] **Step 1: Write the failing test `scripts/test/test_post_linkedin.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/assert.sh"
SKILL="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
POST_TXT="$TMP/post.txt"; printf 'Skill 是函数，不是文档。' > "$POST_TXT"

export SYND_SECRETS="$TMP/none.json"
bash "$SKILL/scripts/post-linkedin.sh" "$POST_TXT"; assert_exit $? 3 "missing creds -> exit 3"

echo '{"linkedin":{"access_token":"tok","author_urn":"urn:li:person:abc"}}' > "$TMP/sec.json"
export SYND_SECRETS="$TMP/sec.json"
OUT="$(bash "$SKILL/scripts/post-linkedin.sh" "$POST_TXT" --dry-run)"; CODE=$?
assert_exit "$CODE" 0 "dry-run with creds -> exit 0"
assert_contains "$OUT" "Skill 是函数" "dry-run echoes the text"
assert_contains "$OUT" "urn:li:person:abc" "dry-run shows author urn"

finish test_post_linkedin
```

- [ ] **Step 2: Run to verify it fails**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_post_linkedin.sh
```
Expected: FAIL (post-linkedin.sh missing)

- [ ] **Step 3: Write `scripts/post-linkedin.sh`**

```bash
#!/usr/bin/env bash
# post-linkedin.sh <post.txt> [--dry-run]  exit: 0 ok / 3 no creds / other fail
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
TXT_FILE="${1:?usage: post-linkedin.sh <post.txt> [--dry-run]}"
DRY="${2:-}"
TEXT="$(cat "$TXT_FILE")"

TOKEN="$(secret '.linkedin.access_token')"
URN="$(secret '.linkedin.author_urn')"
[[ -n "$TOKEN" && -n "$URN" ]] || { echo "linkedin: no creds" >&2; exit 3; }

if [[ "$DRY" == "--dry-run" ]]; then echo "linkedin would post as $URN: $TEXT"; exit 0; fi

body="$(jq -nc --arg urn "$URN" --arg t "$TEXT" '{
  author:$urn, lifecycleState:"PUBLISHED",
  specificContent:{ "com.linkedin.ugc.ShareContent":{
    shareCommentary:{ text:$t }, shareMediaCategory:"NONE" } },
  visibility:{ "com.linkedin.ugc.MemberNetworkVisibility":"PUBLIC" } }')"
resp="$(curl -fsS -X POST "https://api.linkedin.com/v2/ugcPosts" \
  -H "Authorization: Bearer $TOKEN" -H "X-Restli-Protocol-Version: 2.0.0" \
  -H "Content-Type: application/json" -d "$body")" || { echo "linkedin post failed: $resp" >&2; exit 1; }
PID="$(echo "$resp" | jq -r .id)"
[[ -n "$PID" && "$PID" != "null" ]] || { echo "linkedin no post id: $resp" >&2; exit 1; }
echo "url=https://www.linkedin.com/feed/update/$PID"
echo "post_id=$PID"
```

- [ ] **Step 4: Run to verify it passes**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_post_linkedin.sh
```
Expected: `PASS: test_post_linkedin`

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/wjs-syndicating-articles
git add scripts/post-linkedin.sh scripts/test/test_post_linkedin.sh
git commit -q -m "feat: post-linkedin.sh (ugcPosts) + degrade/dry-run tests"
```

---

### Task 8.5: `build-outbox.sh` — TDD

**Files:**
- Create: `scripts/build-outbox.sh`
- Test: `scripts/test/test_build_outbox.sh`

- [ ] **Step 1: Write the failing test `scripts/test/test_build_outbox.sh`**

```bash
#!/usr/bin/env bash
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/assert.sh"
SKILL="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export SYND_CONFIG="$SKILL/config.json"

# fake article folder with a cover image
ARTF="$TMP/2026-05-15-demo"; mkdir -p "$ARTF"
printf 'PNGDATA' > "$ARTF/cover.png"
POST_TXT="$TMP/post.txt"; printf '一套文案走天下。\nhttps://mp.weixin.qq.com/x' > "$POST_TXT"
OUTBOX="$TMP/outbox/2026-05-15-demo"

bash "$SKILL/scripts/build-outbox.sh" "$ARTF" "$POST_TXT" "$OUTBOX"
assert_file "$OUTBOX/post.txt" "post.txt copied"
assert_file "$OUTBOX/image.png" "hero image copied"
assert_file "$OUTBOX/OPEN.md" "OPEN.md written"
assert_contains "$(cat "$OUTBOX/OPEN.md")" "小红书" "OPEN.md mentions xiaohongshu"
assert_contains "$(cat "$OUTBOX/OPEN.md")" "okjike.com" "OPEN.md includes jike compose link"

# folder with no cover but illustration -> uses illustration
ARTF2="$TMP/2026-05-16-demo2"; mkdir -p "$ARTF2"; printf 'X' > "$ARTF2/illustration.png"
OUTBOX2="$TMP/outbox/2026-05-16-demo2"
bash "$SKILL/scripts/build-outbox.sh" "$ARTF2" "$POST_TXT" "$OUTBOX2"
assert_file "$OUTBOX2/image.png" "falls back to illustration.png"

finish test_build_outbox
```

- [ ] **Step 2: Run to verify it fails**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_build_outbox.sh
```
Expected: FAIL (build-outbox.sh missing)

- [ ] **Step 3: Write `scripts/build-outbox.sh`**

```bash
#!/usr/bin/env bash
# build-outbox.sh <article-folder> <post.txt> <outbox-dir>
# Prepares post.txt + image.png + OPEN.md for the manual (outbox-mode) platforms.
set -uo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
ARTF="${1:?article folder}"; POST_TXT="${2:?post.txt}"; OUTBOX="${3:?outbox dir}"
mkdir -p "$OUTBOX"
cp "$POST_TXT" "$OUTBOX/post.txt"

# hero image: cover.png > illustration.png > none
if   [[ -f "$ARTF/cover.png" ]];        then cp "$ARTF/cover.png" "$OUTBOX/image.png"
elif [[ -f "$ARTF/illustration.png" ]]; then cp "$ARTF/illustration.png" "$OUTBOX/image.png"
fi

POST_BODY="$(cat "$OUTBOX/post.txt")"
{
  echo "# 待发件箱 — 手动平台粘贴指引"
  echo
  echo "文案已在 \`post.txt\`（运行 \`--open\` 时会自动进剪贴板）。主图见 \`image.png\`。"
  echo
  echo "## 文案"
  echo
  echo '```'
  echo "$POST_BODY"
  echo '```'
  echo
  for p in $(enabled_platforms); do
    [[ "$(platform_mode "$p")" == "outbox" ]] || continue
    web="$(jq -r --arg p "$p" '.platforms[$p].web_compose // empty' "$CONFIG")"
    case "$p" in
      facebook)    echo "## Facebook";    echo "- 打开：${web:-https://www.facebook.com/}"; echo "- 粘贴文案 → 发布。" ;;
      jike)        echo "## 即刻";        echo "- 打开：${web:-https://web.okjike.com/}"; echo "- 粘贴文案 → 发布。" ;;
      xiaohongshu) echo "## 小红书";      echo "- 这是手机 App 为主：把 \`image.png\` AirDrop 到手机，文案已在剪贴板，App 内发图文笔记。"; [[ -n "$web" ]] && echo "- 或网页创作者后台：$web" ;;
      *)           echo "## $p"; [[ -n "$web" ]] && echo "- 打开：$web"; echo "- 粘贴文案 → 发布。" ;;
    esac
    echo
  done
} > "$OUTBOX/OPEN.md"
echo "outbox=$OUTBOX"
```

- [ ] **Step 4: Run to verify it passes**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_build_outbox.sh
```
Expected: `PASS: test_build_outbox`

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/wjs-syndicating-articles
git add scripts/build-outbox.sh scripts/test/test_build_outbox.sh
git commit -q -m "feat: build-outbox.sh (post.txt+image+OPEN.md) + tests"
```

---

### Task 9: `SKILL.md` orchestrator

**Files:**
- Create: `~/.claude/skills/wjs-syndicating-articles/SKILL.md`

This is the Claude-executed orchestrator. It is markdown instructions, not a script — no unit test (covered by the e2e smoke in Task 10).

- [ ] **Step 1: Write `SKILL.md`**

````markdown
---
name: wjs-syndicating-articles
description: Use when the user wants to auto-syndicate their latest 微信公众号 article across social platforms — picks the newest un-syndicated article, extracts one core copy, auto-posts to API platforms (X / Bluesky / Threads / LinkedIn) and prepares a copy-paste outbox for manual platforms (Facebook / 小红书 / 即刻). Triggers — "分发文章到各平台", "同步到社交平台", "今天的文章发各平台", "/wjs-syndicating-articles".
---

# wjs-syndicating-articles

每天把最新一篇还没分发过的公众号文章，扇出（syndicate）到各社交平台。**一套文案走天下**，有 API 的真发，没 API 的备好待发件箱让你手动粘。

## Core Principles

- **稳定第一**：每个平台是独立步骤，一个失败绝不影响其它。
- **幂等去重**：`state/history.jsonl` 按 `(slug, platform)` 记录；重复跑只补发没成功的，永不重复发。
- **凭证降级**：API 平台缺/过期凭证 → 自动转 outbox（手动），不报错。
- **署名 / CTA 用「王建硕」**（用户全局偏好），不写营销腔、不堆 hashtag/@/emoji（除非原文有）。

## Inputs

```
/wjs-syndicating-articles                 # 选最新未分发文章，走完整流程（默认/定时用）
/wjs-syndicating-articles <article-folder># 显式指定文章
/wjs-syndicating-articles --open          # 交互模式：打开手动平台 web 页 + 文案进剪贴板
/wjs-syndicating-articles --dry-run       # 只草拟，不发、不写 history
/wjs-syndicating-articles --mark <slug> <platform>  # 手动标记某平台已发
```

`SKILL_DIR = ~/.claude/skills/wjs-syndicating-articles`

## Workflow (default / scheduled run)

### Step 0: --mark short-circuit
若调用是 `--mark <slug> <platform>`：`bash $SKILL_DIR/scripts/history.sh record <slug> <platform> posted` 然后告诉用户已标记，结束。

### Step 1: 选文章
```bash
bash $SKILL_DIR/scripts/pick-next-article.sh
```
- 显式指定了 `<article-folder>` 则跳过此脚本，直接用它。
- 输出为空 → 最近文章都分发完了，今天 rest day，结束。
- 记 `FOLDER`，`SLUG=$(basename "$FOLDER")`。

### Step 2: 抽一套核心文案（你来做，不是脚本）
读 `$FOLDER/article.md` 和 `$FOLDER/meta.json`。抽出**一段最 quotable 的核心句/小段，≤120 字**（保证塞进 X 的 280 字符；中文每字算 2），保留王建硕语气。再加一行软 CTA + 文章链接（公众号链接，没有就用 `meta.json` 里信息+ `article_url_base`）。

把最终文案写进 `$SKILL_DIR/outbox/<date>-<SLUG>/post.txt`（先 `mkdir -p`）。`<date>=$(date +%F)`。

`--dry-run` 时：打印 post.txt 内容 + 下面每个平台「将发什么」，**不**继续 Step 3+，结束。

### Step 3: API 平台（逐个 try/catch，真发）
对 `x bluesky threads linkedin` 各跑一次（按 config 里 mode==api 的）：

```bash
# 先去重：tweeting skill 也可能发过 X
if [[ "$P" == "x" ]]; then
  TW_HIST="$HOME/.claude/skills/wjs-tweeting-from-articles/state/history.jsonl"
  if [[ -f "$TW_HIST" ]] && grep -q "\"$SLUG\"" "$TW_HIST" && grep "\"$SLUG\"" "$TW_HIST" | grep -q '"status":"posted"'; then
    bash $SKILL_DIR/scripts/history.sh record "$SLUG" x skipped; continue
  fi
fi
if bash $SKILL_DIR/scripts/history.sh has "$SLUG" "$P"; then continue; fi   # already done

OUT="$(bash $SKILL_DIR/scripts/post-$P.sh "$POST_TXT")"; CODE=$?
case $CODE in
  0) URL="$(echo "$OUT" | sed -n 's/^url=//p')"; PID="$(echo "$OUT" | sed -n 's/^post_id=//p')"
     bash $SKILL_DIR/scripts/history.sh record "$SLUG" "$P" posted "$URL" "$PID" ;;
  3) bash $SKILL_DIR/scripts/history.sh record "$SLUG" "$P" queued "" "" no_creds ;;  # degrade -> outbox
  *) bash $SKILL_DIR/scripts/history.sh record "$SLUG" "$P" failed ;;                 # retry next run
esac
```

### Step 4: 手动平台 → 待发件箱
```bash
OUTBOX="$SKILL_DIR/outbox/$(date +%F)-$SLUG"
bash $SKILL_DIR/scripts/build-outbox.sh "$FOLDER" "$POST_TXT" "$OUTBOX"
for P in facebook xiaohongshu jike zhihu; do
  bash $SKILL_DIR/scripts/history.sh has "$SLUG" "$P" || bash $SKILL_DIR/scripts/history.sh record "$SLUG" "$P" queued
done
```
（degrade 到 outbox 的 API 平台同理已在 history 记为 queued；它们的文案就在同一个 OPEN.md 里。）

### Step 5: 通知 + 汇总
打印一张表：每个平台 status（posted+URL / queued(outbox) / failed / skipped）。  
无人值守（定时）跑：发一条 PushNotification，例：「✅ X、Bluesky 已发；📋 Facebook/小红书/即刻 在 outbox 待粘：$OUTBOX」。  
**不要**在 Step 5 自动开浏览器——那是 `--open` 的事。

## --open mode（交互，发手动平台时）
1. 找到今天的 outbox：`$SKILL_DIR/outbox/$(date +%F)-<SLUG>`（或最新一个）。
2. `cat OUTBOX/post.txt | pbcopy`（文案进剪贴板）。
3. 用 `/browse` skill 打开 config 里 facebook、jike 的 `web_compose`。
4. 小红书：`open "$OUTBOX/image.png"`（Finder 弹出），提示用户 AirDrop 到手机、文案已在剪贴板。
5. 逐个提示：粘贴 → 发布。用户发完某个可 `--mark <slug> <platform>`。

## File Layout
```
$SKILL_DIR/
├── SKILL.md  config.json  secrets.json(gitignored)
├── scripts/  lib.sh history.sh pick-next-article.sh post-*.sh build-outbox.sh
├── outbox/<date>-<slug>/  post.txt image.png OPEN.md
└── state/history.jsonl
```

## 配置 API 平台（可选，配了才真发）
拷 `secrets.json.example` → `secrets.json`，按需填 bluesky / threads / linkedin。不填的平台自动走 outbox。

## Daily 自动化
```
/schedule daily 10:00 /wjs-syndicating-articles
```
````

- [ ] **Step 2: Verify the skill is discoverable (frontmatter parses)**

Run:
```bash
head -3 ~/.claude/skills/wjs-syndicating-articles/SKILL.md
```
Expected: shows `---` then `name: wjs-syndicating-articles`.

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills/wjs-syndicating-articles
git add SKILL.md && git commit -q -m "feat: SKILL.md orchestrator (API fan-out + outbox + open mode)"
```

---

### Task 10: End-to-end dry-run smoke test

**Files:**
- Create: `scripts/test/test_e2e_dryrun.sh`

- [ ] **Step 1: Write `scripts/test/test_e2e_dryrun.sh`**

```bash
#!/usr/bin/env bash
# Exercises the mechanical pipeline (pick -> dry-run posts -> outbox -> history)
# without network or live SKILL.md orchestration.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/assert.sh"
SKILL="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

ART="$TMP/articles"; F="$ART/2026-05-20-demo"; mkdir -p "$F"
printf '手感这东西，得每天练。' > "$F/article.md"
printf 'PNG' > "$F/cover.png"
CFG="$TMP/config.json"; jq --arg d "$ART" '.articles_dir=$d' "$SKILL/config.json" > "$CFG"
export SYND_CONFIG="$CFG"; export SYND_HISTORY="$TMP/history.jsonl"; : > "$SYND_HISTORY"
export SYND_SECRETS="$TMP/none.json"   # no creds -> bluesky/threads/linkedin degrade

# pick
PICK="$(bash "$SKILL/scripts/pick-next-article.sh")"
assert_eq "$(basename "$PICK")" "2026-05-20-demo" "e2e: picks the demo article"

# write post.txt (simulating Claude's Step 2)
OB="$TMP/outbox/2026-05-20-demo"; mkdir -p "$OB"
printf '手感这东西，得每天练。\nhttps://mp.weixin.qq.com/x' > "$OB/post.txt"

# X dry-run ok
bash "$SKILL/scripts/post-x.sh" "$OB/post.txt" --dry-run >/dev/null; assert_exit $? 0 "e2e: x dry-run ok"
# bluesky/threads/linkedin degrade (exit 3) with no creds
bash "$SKILL/scripts/post-bluesky.sh" "$OB/post.txt" >/dev/null 2>&1; assert_exit $? 3 "e2e: bluesky degrades"
bash "$SKILL/scripts/post-threads.sh" "$OB/post.txt" >/dev/null 2>&1; assert_exit $? 3 "e2e: threads degrades"
bash "$SKILL/scripts/post-linkedin.sh" "$OB/post.txt" >/dev/null 2>&1; assert_exit $? 3 "e2e: linkedin degrades"

# outbox builds
bash "$SKILL/scripts/build-outbox.sh" "$F" "$OB/post.txt" "$OB" >/dev/null
assert_file "$OB/OPEN.md" "e2e: outbox OPEN.md exists"
assert_file "$OB/image.png" "e2e: outbox image exists"

finish test_e2e_dryrun
```

- [ ] **Step 2: Run it**

Run:
```bash
bash ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_e2e_dryrun.sh
```
Expected: `PASS: test_e2e_dryrun`

- [ ] **Step 3: Run the whole suite**

Run:
```bash
for t in ~/.claude/skills/wjs-syndicating-articles/scripts/test/test_*.sh; do bash "$t" || echo "SUITE FAIL: $t"; done
```
Expected: every line ends in `PASS: ...`, no `SUITE FAIL`.

- [ ] **Step 4: Commit**

```bash
cd ~/.claude/skills/wjs-syndicating-articles
git add scripts/test/test_e2e_dryrun.sh
git commit -q -m "test: end-to-end dry-run smoke"
```

---

### Task 11: Manual verification (live) + schedule wiring

**Files:** none (operational)

- [ ] **Step 1: Real X post on a real article (the one live check that matters)**

Pick a real article folder, write a short `post.txt`, and post for real:
```bash
SKILL=~/.claude/skills/wjs-syndicating-articles
printf '手感这东西，得每天练。' > /tmp/pt.txt
bash $SKILL/scripts/post-x.sh /tmp/pt.txt
```
Expected: prints `url=https://x.com/jianshuo/status/...`; open the URL and confirm the tweet. Delete it after if it was a test.

- [ ] **Step 2: (If user has creds) configure `secrets.json` and live-test one more platform**

```bash
cp ~/.claude/skills/wjs-syndicating-articles/secrets.json.example ~/.claude/skills/wjs-syndicating-articles/secrets.json
# edit in real bluesky handle + app password, then:
bash ~/.claude/skills/wjs-syndicating-articles/scripts/post-bluesky.sh /tmp/pt.txt
```
Expected: prints a `bsky.app` url; confirm the post. If user has no creds, skip — platform stays in outbox mode (already covered by tests).

- [ ] **Step 3: Dry-run the full skill through Claude**

In Claude Code: `/wjs-syndicating-articles --dry-run`
Expected: picks newest un-syndicated article, prints the drafted copy + per-platform preview, writes nothing to history.

- [ ] **Step 4: Wire the daily schedule**

```
/schedule daily 10:00 /wjs-syndicating-articles
```
Confirm it appears in `/schedule` list.

- [ ] **Step 5: Final commit**

```bash
cd ~/.claude/skills/wjs-syndicating-articles
git add -A && git commit -q -m "chore: verified live X post + daily schedule wired" || true
```

---

## Notes for the implementer

- **Make scripts executable** if you prefer (`chmod +x scripts/*.sh`); all run via `bash <path>` so it's optional.
- **`set -euo pipefail`** is on in `lib.sh`-sourcing scripts. In `history.sh has`, the `jq -e ... || exit 1` pattern is deliberate — don't let `set -e` swallow the intended non-zero.
- **Never commit `secrets.json`** — it's gitignored in Task 1; double-check before any push.
- **`--mark`** is a convenience; status-writeback after manual posting is optional, per spec (out of scope to enforce).
