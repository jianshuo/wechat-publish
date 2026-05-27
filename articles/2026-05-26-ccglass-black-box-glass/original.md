用户指令：帮我写一篇文章，技术细节范儿，列出来最近的一些版本的所有功能，原理，背后的思考以及好处。

来源材料（ccglass 仓库，2026-05-22 到 2026-05-26，v0.2.0 → v0.6.0）：

核心原理：coding agent 这些 CLI 忽略 HTTP_PROXY/HTTPS_PROXY，抓包工具看不到。ccglass 让 client 自己跟真 API 做 HTTPS，只截 localhost 那段明文 HTTP。无需 CA 证书、无需破 TLS。

最近版本功能：
- provider 抽象：Claude/Codex/Codex-Azure/DeepSeek-TUI/Reasonix/Kimi/OpenCode/Ollama/LM Studio/OpenRouter/GLM/Bedrock/Vertex。三元组：包哪个命令 + 改哪个 env var + 什么 wire format。
- Reasonix CLI provider (#49)
- 智能 upstream 解析：Codex 从 config.toml 读 base_url (#43)；Bedrock 用 ANTHROPIC_BEDROCK_BASE_URL (#38)；provider switcher 写在 env 的 ANTHROPIC_BASE_URL 也捡 (#41)
- 检测 ChatGPT auth/websocket 模式并警告 (#28)：codex doctor 检测，chatgpt 模式 dashboard 空，主动提示切 API-key
- content-addressed (git 式) 存储 (#45)：message/tools/system 按 hash 存一次，避免长会话 O(n²)。repack / rm 命令
- 日志存 ~/.ccglass/sessions/ 不怕删项目 (#39)，配 migrate
- 跨 session token 用量汇总 (#48)
- dashboard 升级 (#50)：per-request latency、TTFT、tok/s、latency trend sparkline、per-model filter、session summary、light/dark theme
- copy as cURL
- 错误/重试循环显示 (#18)
- 自检 MCP：包 Claude Code 时注册 query 工具，agent 在 chat 里查自己刚发的请求
