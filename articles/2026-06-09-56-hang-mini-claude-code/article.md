我用了 56 行代码，大致的实现了一个编程  Agent， 基本上就是 Claude Code的核心功能。大家可以看看。



我用 Moonshot 的接口写了一个，放到 GitHub 上了。整个程序就三件事。

**工具是什么？**

工具是模型能用的手。我给了他三只手：

- `read_file`：读一个文件
- `list_files`：看目录里有什么
- `edit_file`：把东西写进文件

就这三只手，他就能读代码、看目录结构、改程序。代码长这样：

<section style="background:#f6f8fa;border-radius:6px;padding:14px 16px;overflow-x:auto;font-family:Menlo,Consolas,monospace;font-size:14px;line-height:1.8;color:#24292e;">fn("read_file",  "读文件", { path })<br>fn("list_files", "列目录", { path })<br>fn("edit_file",  "写文件", { path, content })</section>

**循环是什么？**

循环就是不停地让他做事，直到他说「我做完了」。

每次把问题和对话历史一起发给模型，他决定要不要用工具。要用，就执行工具、把结果告诉他；不用了，他直接回答，这轮结束。

<section style="background:#f6f8fa;border-radius:6px;padding:14px 16px;overflow-x:auto;font-family:Menlo,Consolas,monospace;font-size:14px;line-height:1.8;color:#24292e;">while (true) {<br>  问模型：下一步做什么？<br>  如果他要用工具 → 执行工具，结果告诉他<br>  如果不用了 → 这轮结束<br>}</section>

**记忆是什么？**

每次问他之前，把之前所有的对话都一起发过去——包括他之前用工具得到的结果。他才能记得做到哪一步了。

<span style="color:#c0392b;">工具、循环、记忆，三件事，就是一个能干活的编程助手。</span>

搓完这个，我才真的明白 Claude Code 在做什么。

他在「想」的时候，是模型在决定下一步该用哪只手。他在「执行」的时候，是代码在真的读文件、写文件。不是魔法，是一个有手的对话循环。

<span style="color:#c0392b;">拆开盒子，才能真正用好它。</span>

这个叫 `mini-claude-code`，没有错误恢复，没有 streaming，没有预算管理。这是我给自己理解用的玩具，别人用估计磕磕绊绊。但他能跑，跑起来你就知道 Claude Code 骨子里是什么了。

![](./illustration.png)

代码在 https://github.com/jianshuo/mini-claude-code，56 行，自己看。
