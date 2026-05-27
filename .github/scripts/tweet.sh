#!/usr/bin/env bash
# Pick the newest article that hasn't been tweeted yet, ask Claude (headless,
# via CLAUDE_CODE_OAUTH_TOKEN) to draft + pick one tweet, post it with xurl,
# and append the record to tweet-state/history.jsonl.
#
# Runs in GitHub Actions (ubuntu, no proxy needed). Dedup is by slug in
# tweet-state/history.jsonl. Set DRY_RUN=1 to draft + log without posting.
set -uo pipefail

cd "$(git rev-parse --show-toplevel)"
STATE_DIR="tweet-state"
HISTORY="${STATE_DIR}/history.jsonl"
mkdir -p "$STATE_DIR"
touch "$HISTORY"
today="$(date +%F)"

for bin in claude xurl jq; do
  command -v "$bin" >/dev/null 2>&1 || { echo "FATAL: missing $bin"; exit 1; }
done

# --- Step 1: pick newest un-posted article (folder name is YYYY-MM-DD-slug) ---
posted="$(grep -h '"status":"posted"' "$HISTORY" 2>/dev/null \
          | grep -oE '"slug":"[^"]+"' | sed -E 's/"slug":"([^"]+)"/\1/' | sort -u)"
FOLDER=""
while IFS= read -r d; do
  d="${d%/}"
  slug="$(basename "$d")"
  [[ -f "$d/article.md" ]] || continue
  if ! grep -qxF "$slug" <<<"$posted"; then FOLDER="$d"; break; fi
done < <(ls -d articles/*/ 2>/dev/null | sort -r)

if [[ -z "$FOLDER" ]]; then
  echo "No un-posted article — rest."
  echo "{\"date\":\"${today}\",\"status\":\"rest_day\"}" >> "$HISTORY"
  exit 0
fi
SLUG="$(basename "$FOLDER")"
echo "Picked: $FOLDER (slug: $SLUG)"

# --- Step 2: Claude drafts + picks ---
TWEET_FILE="$(mktemp)"
ANGLE_FILE="$(mktemp)"
prompt=$(cat <<EOF
Read the article at:
  ${FOLDER}/article.md

Draft 3 tweet candidates for X (Twitter), each from a different angle:
- A · 金句 — quote the strongest single sentence (or short couplet) from the article, optionally with a one-line lead-in
- B · 反差 — sharp "not X, is Y" cognitive flip
- C · 小灾难 — the "every day, most attempts fail, but failure is the data" rhythm

Hard constraints on each candidate:
- ≤ 140 Chinese characters (X allows 280 latin = 140 CJK characters)
- Preserve 王建硕 voice: plain, honest, conversational, family-style metaphors
- NO hashtags, NO @mentions, NO emoji (unless original article has them), NO marketing tone
- Material MUST come from the article text — do not invent new examples
- NO mp.weixin link, NO "click here", NO call-to-action

Then pick the strongest of the 3 (most resonance + tightest line).

Write ONLY the chosen tweet text (exactly what should be posted, no quotes, no metadata) to:
  ${TWEET_FILE}

Write the letter (A or B or C) to:
  ${ANGLE_FILE}

Do not output anything else. Just write those two files.
EOF
)

echo "→ asking Claude to draft + pick ..."
claude -p --allowedTools=Read,Write -- "$prompt" || {
  echo "FATAL: claude drafting failed"
  echo "{\"date\":\"${today}\",\"slug\":\"${SLUG}\",\"status\":\"draft_failed\"}" >> "$HISTORY"
  exit 1
}

[[ -s "$TWEET_FILE" ]] || {
  echo "FATAL: claude did not write tweet text"
  echo "{\"date\":\"${today}\",\"slug\":\"${SLUG}\",\"status\":\"no_tweet_file\"}" >> "$HISTORY"
  exit 1
}
TWEET_TEXT="$(cat "$TWEET_FILE")"
ANGLE="$(tr -d '\r\n ' < "$ANGLE_FILE" 2>/dev/null || echo '?')"
CHARS="$(printf '%s' "$TWEET_TEXT" | wc -m | tr -d ' ')"
echo "Angle: $ANGLE  Chars: $CHARS"
echo "--- tweet ---"; echo "$TWEET_TEXT"; echo "--- end ---"

# --- Step 3: post ---
if [[ "${DRY_RUN:-0}" == "1" ]]; then
  echo "DRY_RUN — not posting."
  TEXT_JSON="$(printf '%s' "$TWEET_TEXT" | jq -Rs .)"
  echo "{\"date\":\"${today}\",\"slug\":\"${SLUG}\",\"angle\":\"${ANGLE}\",\"chars\":${CHARS},\"status\":\"dry_run\",\"text\":${TEXT_JSON}}" >> "$HISTORY"
  exit 0
fi

JSON="$(jq -nc --arg text "$TWEET_TEXT" '{text:$text}')"
resp="$(xurl -X POST -d "$JSON" /2/tweets 2>&1)"
TWEET_ID="$(printf '%s' "$resp" | grep -oE '"id":"[0-9]+"' | head -1 | sed -E 's/.*"([0-9]+)".*/\1/')"
if [[ -z "$TWEET_ID" ]]; then
  echo "FATAL: post returned no id"; echo "$resp"
  echo "{\"date\":\"${today}\",\"slug\":\"${SLUG}\",\"angle\":\"${ANGLE}\",\"status\":\"post_failed\"}" >> "$HISTORY"
  exit 1
fi
TWEET_URL="https://x.com/jianshuo/status/${TWEET_ID}"
echo "✓ Posted: $TWEET_URL"

# --- Step 4: history ---
TEXT_JSON="$(printf '%s' "$TWEET_TEXT" | jq -Rs .)"
echo "{\"date\":\"${today}\",\"slug\":\"${SLUG}\",\"angle\":\"${ANGLE}\",\"chars\":${CHARS},\"tweet_id\":\"${TWEET_ID}\",\"tweet_url\":\"${TWEET_URL}\",\"text\":${TEXT_JSON},\"status\":\"posted\"}" >> "$HISTORY"
echo "done."
