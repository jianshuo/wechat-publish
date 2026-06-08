# 我的十一条 Claude Code 使用经验

简单记录一下到目前为止，Claude Code 的经验，纯个人探索，不见得适用于所有人。

1. 盯住一个工具猛用。我用 Claude Code。我并不认为他比 Codex 更好，但是<span style="color:#c0392b;">比较工具花费的精力 ROI 不见得高</span>，虽然能把差异说得头头是道，给人虚假的成就感更高。

2. 记住最重要的快捷键。`Control+G` 打开编辑器，帮助写长一点的内容；`Control+A`、`Control+E`、`Control+U` 这些在命令行非常实用的快速移动光标的快捷键。虽然不是 AI 时代新的，却在使用的时候和 `Control+C`、`Control+V` 一样重要。

3. 使用语音输入。HoldSpeak 很有帮助。

4. 一个项目先写 PROJECT.md，用结构化的方法先把想到的一次性写出来。

5. Claude agents 是缺省打开方式。

6. Claude Code 和 github.com 和 cloudflare.com 是绝配，<span style="color:#c0392b;">把构建过程、发布过程，以及域名相关的所有操作交给基础设施</span>。

7. 分开人写的和机器写的。手工维护最核心的 CLAUDE.md，不要去读 Claude Code 写的 .md 或者代码。机器归机器，人类归人类。AI 写的东西用问 AI 的方式了解，不要看源代码。

8. 拖拽文件进 Claude Code 的窗口——音频、视频、文档、截屏——讲不清楚用 `Command+Shift+5` 截屏，然后拖过去，最快。

9. <span style="color:#c0392b;">重构记忆系统。</span>以 ~/.claude/CLAUDE.md 为中心，分门别类引用多个 memory 文件，要求不使用项目的 memory，并且把所有的 memory 文件放在 git 里面，同步到 github（private），这样自己的记忆才是永久的、可积累的，不至于散落在每个项目里面。

10. 写 Skill，同时每次工作结束以后，要求 Claude 「沉淀学到的到 Skill 里」——可以让他自动做。

11. 有可能的情况下，对于复杂任务使用 ultracode 触发 dynamic workflow。虽然很贵，虽然很慢，但是<span style="color:#c0392b;">效果还是有保证的</span>。

就这些。用着用着，自然会找到自己的节奏。
