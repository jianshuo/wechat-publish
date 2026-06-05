# X Tweet Rewrite Playground Design

## Goal

Build an experimental local playground for comparing rewrites of the user's X posts. The source is `x-weekly` in this repository. The playground lists original non-reply tweets on the left, accepts many rewrite prompts, runs each prompt against every tweet, and shows each prompt's output as a comparable version column.

## Source Data

The canonical source is the structured X API cache under `x-weekly/.cache/tweets-*.json`. The app uses the newest cache file by default and reads `data[]` from that JSON.

Filtering rules:

- Include tweets authored by the cached user.
- Exclude retweets because the archive script already fetched with `exclude=retweets`.
- Exclude replies: any tweet with `referenced_tweets` containing `{ "type": "replied_to" }`, or with `in_reply_to_user_id`.
- Keep standalone tweets and quote tweets. Quote tweets are not replies and are useful rewrite material.
- Sort tweets by `created_at` ascending so the list reads chronologically.

Each tweet record exposed to the UI contains `id`, `created_at`, `text`, `url` when derivable, metrics when present, and a `kind` of `tweet` or `quote`.

## Architecture

Use one small local Python server in `tools/x_tweet_playground.py`.

Responsibilities:

- Serve the browser UI from `playground/`.
- Load and filter tweets from the latest `x-weekly/.cache/tweets-*.json`.
- Expose `GET /api/tweets` for the UI.
- Expose `POST /api/rewrite` with `{ prompt, tweets }`.
- Call an LLM provider from the server and return `{ prompt, versions: [{ id, text }] }`.

The browser UI stays framework-free: `playground/index.html`, `playground/styles.css`, and `playground/app.js`. This matches the repo's lightweight generated-content nature and avoids adding package management.

## LLM Configuration

The server reads environment variables:

- `OPENAI_API_KEY` for authentication.
- `OPENAI_MODEL` for the model name.

The rewrite endpoint sends one batch request containing all tweet texts and the user's prompt. The system instruction requires:

- Preserve the original meaning.
- Rewrite each tweet independently.
- Return valid JSON only.
- Keep the same order and IDs.

If the API key or model name is missing, `/api/rewrite` returns a clear configuration error. The UI displays that error in the prompt column instead of failing silently.

## UI

The first screen is the working tool, not a landing page.

Layout:

- Top bar: prompt textarea, model/status indicator, and a run button.
- Left fixed column: original tweets, with date/time and compact metrics.
- Right comparison area: one column per prompt run.

Behavior:

- On load, fetch and render the original tweets.
- When the user submits a prompt, create a new version column immediately with a loading state.
- On success, fill each row with the rewritten text for that prompt.
- On failure, keep the column and show the error message.
- Allow many prompt columns in one session.
- Keep original and rewritten rows aligned by tweet ID.

The UI does not save prompt history to disk in the first version. Refreshing the page resets prompt columns; source tweets are reloaded from `x-weekly`.

## Error Handling

- Missing or invalid cache file: server returns an explicit `/api/tweets` error with the searched path.
- No non-reply tweets: UI shows an empty state.
- LLM failure: prompt column shows the server error and can be retried by running the prompt again.
- Malformed LLM JSON: server reports a parse error and includes enough context in server logs for debugging, without dumping secrets.

## Testing

Add focused Python unit tests for:

- Selecting the newest cache file.
- Filtering replies while keeping quote tweets.
- Sorting tweets chronologically.
- Parsing valid LLM JSON into ID-matched rewrite results.

Manual verification:

- Start the local server.
- Open the playground in a browser.
- Confirm originals load from `x-weekly`.
- Run a prompt with a configured API key.
- Confirm a new comparison column appears and all rows align.
