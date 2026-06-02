# X 周记 · 5月11日–5月17日

> 本周在 X 上的发帖归档（原创 + 回复），共 2 条。

## 周三 5月13日

**22:29**　Whisper API 直接吐的 SRT，几乎不能用。

两个失败模式：
- 30 秒一大块字幕，没人读得完
- 安静段循环幻觉「你很难的」× 50

修法：response_format=verbose_json + timestamp_granularities[]=word，自己拼 cue。

别让不懂你需求的工具替你做边界决定。

源码：https://t.co/dKQ0jmi3ha https://t.co/Hk5S8iOhf5
<small>💬3 ♥14 🔁2</small>

**22:34**　机器翻译进中文，处处都是「这个」「那个」「那份」「那种」。

不是翻译错了 —— 中文是 high-context 语言，源语言里多数指代都该删掉。

「那份能量」→ 「能量」
「正是在这合一里」→ 「合一中」

规则写进 prompt，AI 就照着改。

源码：https://t.co/ViA4q9XAG9 https://t.co/D1tnyNVceO
<small>💬2 ♥10 🔁0</small>
