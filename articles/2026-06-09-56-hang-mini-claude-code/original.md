用王建硕口吻写一篇文章：56行代码手搓一个 Claude Code

基于 mini-claude-code 项目（https://github.com/jianshuo/mini-claude-code）
- code.js：56行，用 Moonshot/Kimi API，OpenAI-compatible
- 三个工具：read_file、list_files、edit_file
- agent loop：while true，不断调工具直到模型不再调用为止
