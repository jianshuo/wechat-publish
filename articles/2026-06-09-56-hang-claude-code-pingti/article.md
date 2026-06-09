Claude Code 虽然很复杂（50 万行），但是却非常精巧。<span style="color:#c0392b;">从本质上来说，就是两层 `while(true) {}` 的循环，组织起来的读写查文件三个工具调用。</span>我用了 56 行，复刻了一下 Claude Code 的最核心代码，虽然不能真的做到平替，但是写些简单的代码是可以的，最主要是理解 Claude Code（或者大多数 Agent）的工作原理。以下是全部代码，Github 源代码放在「查看原文」里面。

```javascript
import OpenAI from "openai";
import fs from "fs";
import path from "path";
import readline from "readline";

const client = new OpenAI({ apiKey: process.env.MOONSHOT_API_KEY, baseURL: "https://api.moonshot.cn/v1" });

const fn = (name, desc, props, req = []) => ({
    type: "function",
    function: { name, description: desc, parameters: { type: "object", properties: props, required: req } },
});

const TOOLS = [
    fn("read_file",  "Read a file.",               { path: { type: "string" } },                               ["path"]),
    fn("list_files", "List files in a directory.", { path: { type: "string" } }),
    fn("edit_file",  "Write content to a file.",   { path: { type: "string" }, content: { type: "string" } }, ["path", "content"]),
];

function runTool(name, input) {
    try {
        if (name === "read_file")  return fs.readFileSync(input.path, "utf8");
        if (name === "list_files") return fs.readdirSync(input.path ?? ".").sort().join("\n");
        if (name === "edit_file") {
            fs.mkdirSync(path.dirname(path.resolve(input.path)), { recursive: true });
            fs.writeFileSync(input.path, input.content);
            return `Wrote ${input.content.length} bytes to ${input.path}`;
        }
    } catch (e) { return `Error: ${e.message}`; }
}

async function agentLoop(userMessage, history) {
    history.push({ role: "user", content: userMessage });
    while (true) {
        const { choices } = await client.chat.completions.create({ model: "moonshot-v1-8k", tools: TOOLS, tool_choice: "auto", messages: history });
        const msg = choices[0].message;
        history.push(msg);
        if (msg.content) console.log(`\nAssistant: ${msg.content}`);
        if (!msg.tool_calls?.length) return;
        for (const tc of msg.tool_calls) {
            const input = JSON.parse(tc.function.arguments);
            console.log(`  → ${tc.function.name}(${tc.function.arguments})`);
            const out = runTool(tc.function.name, input);
            console.log(`  ← ${String(out).slice(0, 120)}`);
            history.push({ role: "tool", tool_call_id: tc.id, content: out });
        }
    }
}

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const ask = q => new Promise(r => rl.question(q, r));
const history = [{ role: "system", content: "You are a coding assistant. Use tools to read, list, and edit files — never guess file contents. Always call a tool when the task involves the filesystem. Always output code into filesystem" }];
console.log("Mini Code Assistant (Kimi) — press Ctrl+C to exit\n");
while (true) {
    const msg = (await ask("You: ")).trim();
    if (msg) await agentLoop(msg, history);
}
```

**两层循环**

最外层，就是最后四句，收到一个用户输入，把它和历史一起开启一个内部的小循环。

```javascript
while (true) {
    const msg = (await ask("You: ")).trim();
    if (msg) await agentLoop(msg, history);
}
```

这是大循环。

这是那个内部的小循环：

```javascript
while (true) {
    const { choices } = await client.chat.completions.create({ model: "moonshot-v1-8k", tools: TOOLS, tool_choice: "auto", messages: history });
    const msg = choices[0].message;
    history.push(msg);
    if (msg.content) console.log(`\nAssistant: ${msg.content}`);
    if (!msg.tool_calls?.length) return;
    for (const tc of msg.tool_calls) {
        const input = JSON.parse(tc.function.arguments);
        console.log(`  → ${tc.function.name}(${tc.function.arguments})`);
        const out = runTool(tc.function.name, input);
        console.log(`  ← ${String(out).slice(0, 120)}`);
        history.push({ role: "tool", tool_call_id: tc.id, content: out });
    }
}
```

两个都是死循环。

前一个大循环（User Loop），只有当用户输入 `Ctrl+C` 强行中断的时候跳出，第二个小循环，只有当 `tool_calls.length == 0` 的时候跳出。<span style="color:#c0392b;">也就是说，只有 LLM 回复要求的工具调用都调用完毕以后，这一轮交互才算真正结束。</span>

最里面有一个很小的循环，就是如果 LLM 同时要调用多个工具，就一个一个按顺序调用本地的工具完成。

没了。就这么简单。主要代码完毕。

**工具定义**

上面就是两个函数定义了一下工具。一个是真正的定义，里面只定义了三个代码 Agent 至少要用的工具：一个是读文件，一个是读文件夹内容，一个是写文件。都是最简单的文件操作。当然 Claude Code 内置了四十几个工具，大家可以从泄漏的代码的 Tools 文件夹里面看到，每一个工具的定义不比我下面定义的复杂多少。

```javascript
const fn = (name, desc, props, req = []) => ({
    type: "function",
    function: { name, description: desc, parameters: { type: "object", properties: props, required: req } },
});

const TOOLS = [
    fn("read_file",  "Read a file.",               { path: { type: "string" } },                               ["path"]),
    fn("list_files", "List files in a directory.", { path: { type: "string" } }),
    fn("edit_file",  "Write content to a file.",   { path: { type: "string" }, content: { type: "string" } }, ["path", "content"]),
];

function runTool(name, input) {
    try {
        if (name === "read_file")  return fs.readFileSync(input.path, "utf8");
        if (name === "list_files") return fs.readdirSync(input.path ?? ".").sort().join("\n");
        if (name === "edit_file") {
            fs.mkdirSync(path.dirname(path.resolve(input.path)), { recursive: true });
            fs.writeFileSync(input.path, input.content);
            return `Wrote ${input.content.length} bytes to ${input.path}`;
        }
    } catch (e) { return `Error: ${e.message}`; }
}
```

在后面就是把这几个工具变成一个 JSON 数据传给 LLM 就好了。

最终生成的 JSON 格式就是这样，原封不动的给大模型就行：

```javascript
[
  {
    type: 'function',
    function: {
      name: 'read_file',
      description: 'Read a file.',
      parameters: [Object]
    }
  },
  ...
]
```

LLM 会根据上下文和你提供的工具，找到合适的工具，把最终的项目完成。

<span style="color:#c0392b;">就是这简单的 56 行，是大多数 Coding Agent 的骨架。</span>在这之上可以加很多更多的功能，比如 Skills 的支持等。

![](./illustration.png)
