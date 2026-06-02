# X 周记 · 5月4日–5月10日

> 本周在 X 上的发帖归档（原创 + 回复），共 7 条。

## 周四 5月7日

**00:22**　AI feedback in serif type reads like a letter, not a chat bubble. That's intentional.

Cathier uses Instrument Serif for all AI reflections — not aesthetics, but pacing. Same words, 40% longer dwell time in testing. Type is rhythm.

(App Store: search Cathier) https://t.co/sytoz8c9fj
<small>💬0 ♥2 🔁0</small>

## 周六 5月9日

**23:59**　Just shipped /multicam — a Claude Code skill for multi-cam footage.

→ audio sync via envelope cross-correlation (handles low SNR + clock drift)
→ director-style auto-edit (Viterbi over per-second scores)
→ PiP, virtual crop-zoom, partial-coverage sources

#ClaudeCode
<small>💬0 ♥1 🔁0</small>

## 周日 5月10日

**00:14**　Just shipped /translate-video — end-to-end video localization.

→ Whisper transcribe → translated SRT (zh / en first-class)
→ time-aligned TTS dub: Volcano 豆包 + edge-tts neural
→ burn-in, original-audio bed, mouth-movement diarization

https://t.co/hgfZ81TAto
#ClaudeCode
<small>💬0 ♥4 🔁0</small>

**00:16**　Just shipped /jianshuo-wechat-mp-publish — Claude Code skill for 微信公众号 articles.

→ light polish, never overwrites your voice
→ auto cover (2.45:1) + illustration via gpt-image-2
→ rich-text clipboard publish helper, ~2 min to ship

https://t.co/UU6Xjhw5Dv
#ClaudeCode
<small>💬0 ♥1 🔁0</small>

**15:19**　AI 时代最反直觉的一件事：要学的越多，越应该学得越少。

不是少学，是少而精——选一两个真正想解决的问题，沿着问题学。

其余的，让 AI 帮你查。
<small>💬1 ♥6 🔁2</small>

**23:01**　微信公众号 skill 更新了 — 修了一个会让题图横向文字被裁掉的 bug。

之前 SKILL.md 和 cover-prompt.md 把比例写成 2.45:1, 但脚本实际裁到 900×383 (= 2.35:1)。AI 按 2.45 构图, 裁剪时左右各被切掉一截。

9 处统一为 2.35:1。

https://t.co/UU6Xjhw5Dv
#ClaudeCode
<small>💬2 ♥5 🔁0</small>

**23:04**　translate-video skill 更新 — 加了三道用户确认门, 防止误触烧 CPU/烧 API:

🛑 烧入字幕前: 先渲 30s 预览 + 抽帧 + 你确认字号才跑全片
🛑 全片配音前: 强制 sample 3-4 个 voice 让你挑
🛑 承诺 Volcano 声音前: 5 词 smoke test, 401 直接提示去开通

https://t.co/hgfZ81TAto
#ClaudeCode
<small>💬0 ♥1 🔁0</small>
