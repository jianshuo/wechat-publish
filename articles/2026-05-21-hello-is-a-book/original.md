原始素材：claude-logs/2026-05-21T13-38-34-080Z_5umg.request.readable.md

这是一次真实的 Claude API 请求抓包。用户在终端里只敲了一个词："hello"。
但实际发出去的 HTTP 请求体是 137,918 字节 / 141,389 字符。

拆开看：
- 真正你打的字：hello，5 个字符
- 41 个工具的完整 JSON 说明书：约 87KB（占六成）
- 技能清单（469 行）、记忆、几个外部插件（imessage/telegram/vercel）的使用须知、各种 system-reminder：约 45KB
- "你是谁、你该怎么做事"的系统身份说明：约 7KB

标题：你以为说了一句话？不是，你发过去一本三国演义
