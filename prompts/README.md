# prompts/

Per-platform writing prompts. Each subfolder is one platform; its `prompt.md`
tells Claude how to turn a 王建硕 公众号 article into content for that platform.

```
prompts/
  x/prompt.md            ← used by .github/scripts/tweet.sh (the every-6h Action)
  bluesky/prompt.md
  threads/prompt.md
  linkedin/prompt.md
  facebook/prompt.md
  xiaohongshu/prompt.md
  jike/prompt.md
  zhihu/prompt.md
```

## Convention

A `prompt.md` is a template. Automation substitutes these placeholders before
sending it to Claude headless:

| Placeholder        | Replaced with                                            |
|--------------------|----------------------------------------------------------|
| `{{ARTICLE_PATH}}` | absolute path to the source `article.md`                 |
| `{{OUT_FILE}}`     | file Claude must write the final post text to            |
| `{{ANGLE_FILE}}`   | (X only) file Claude must write the chosen angle letter  |

Shared house rules (apply to every platform unless its prompt overrides):

- Preserve 王建硕 voice: plain, honest, conversational, family-style metaphors.
- Material must come from the article — never invent examples.
- Any subscribe / follow / CTA uses the name **王建硕** (never "AI 炼金术" etc.).
- No marketing tone.

Editing a `prompt.md` changes the output immediately on the next run — no code
change needed.
