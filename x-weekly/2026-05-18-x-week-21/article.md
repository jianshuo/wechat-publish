# X 周记 · 5月18日–5月24日

> 本周在 X 上的发帖归档（原创 + 回复），共 30 条。

## 周一 5月18日

**15:13**　每天写一段 prompt，跟每天画一幅画是一回事。

不是非要写得多漂亮，就是让今天的句子跟昨天有点不一样。

不是变聪明，是手感来了。
<small>💬0 ♥0 🔁0</small>

> ↩️ 回复 @garrytan：https://t.co/XTqXqWuQn5
**23:26**　@garrytan Book Mirror is a great idea. I just did the mirroring - suddenly changes any book into interesting one.
<small>💬0 ♥0 🔁0</small>

**23:27**　https://t.co/Raznaxn5uv
<small>💬0 ♥0 🔁0</small>

## 周四 5月21日

> 🔁 引用 @jinchenma_ai：AI 会取代程序员，但是个渐进过程，不是某天突然清场。 更准确的说法是说，AI 是一种高度集中化的技术，它让少数人更强，让大多数人失去原有价值。 软件工程的终局…
**21:33**　我半年前是这个观点，现在我确认只会用现代编程语言（Python，C等）的程序员已经全部失业了，只是他们的老板们还没有发现。这个过程已经完结了，是瞬间的事情，只是需要一个渐进的过程才会被人意识到。 https://t.co/3vG4Xwn9aP
<small>💬1 ♥7 🔁2</small>

## 周五 5月22日

**22:54**　用 Claude Code，在没有上下文时给它打一个词：hello。
你猜它实际发出去多少？
我把这次请求抓下来一看：137918 个字节，十三万多字符，一本书那么厚。
我打的那个 hello，只占 5 个字符。 https://t.co/RFYUN59oKd
<small>💬3 ♥12 🔁1</small>

> ↩️ 回复 @jianshuo：用 Claude Code，在没有上下文时给它打一个词：hello。 你猜它实际发出去多少？ 我把这次请求抓下来一看：137918 个字节，十三万多字符，一本书…
**22:54**　剩下的十三万多，全是它每次随身背着的东西：41 个工具的完整说明书（占六成）、四百多条技能清单、一份记忆、几个插件须知、一段「你是谁、该怎么做事」的身份说明。
你打一个 hello，这一整套跟着一起发过去。
<small>💬1 ♥0 🔁0</small>

> ↩️ 回复 @jianshuo：剩下的十三万多，全是它每次随身背着的东西：41 个工具的完整说明书（占六成）、四百多条技能清单、一份记忆、几个插件须知、一段「你是谁、该怎么做事」的身份说明。 …
**22:54**　为什么这么干？因为它没有「昨天」。
它每次睁眼都是失忆的，上一句说完就忘干净。所以你每递一句话，系统都得把它该知道的一切重塞一遍。
它不是在「记得」，是每一次都重新读一遍这本书。
<small>💬1 ♥0 🔁0</small>

> ↩️ 回复 @jianshuo：为什么这么干？因为它没有「昨天」。 它每次睁眼都是失忆的，上一句说完就忘干净。所以你每递一句话，系统都得把它该知道的一切重塞一遍。 它不是在「记得」，是每一次都…
**22:54**　好消息是：读过的部分会被缓存。同一本书第二次读，花的时间和钱，都远小于第一次。
<small>💬1 ♥0 🔁0</small>

> ↩️ 回复 @jianshuo：好消息是：读过的部分会被缓存。同一本书第二次读，花的时间和钱，都远小于第一次。
**22:54**　而且这还只是没上下文时。多聊几轮，你的输入、它的输出、每次工具调用的结果、所有中间变量，都一层层往上叠。
Claude Code 的上下文是一百万词元，一部《三国演义》才七十五万。
用不了多久，你每打一个词，它收到的就是一整本《三国演义》。
<small>💬1 ♥0 🔁0</small>

> ↩️ 回复 @jianshuo：而且这还只是没上下文时。多聊几轮，你的输入、它的输出、每次工具调用的结果、所有中间变量，都一层层往上叠。 Claude Code 的上下文是一百万词元，一部《三…
**22:54**　你用 Claude Code 根本不是在聊天。
你是在借一大批工具、和你自己都没意识到的技能，替你垫背景。就像写 C 语言：你只敲一行，一编译，几十万行库代码跟着一起进去。
这，就是 ChatGPT 和 Claude Code 的区别。
<small>💬1 ♥0 🔁0</small>

> ↩️ 回复 @jianshuo：你用 Claude Code 根本不是在聊天。 你是在借一大批工具、和你自己都没意识到的技能，替你垫背景。就像写 C 语言：你只敲一行，一编译，几十万行库代码跟…
**22:54**　全世界用的是同一个模型——版本号一样，就没有一丝区别。
人和人的差别，全在这一大坨随身带着的信息里。它越厚，越精确地刻画出你是谁。
模型是同一个。那本书，才是你。
<small>💬0 ♥3 🔁1</small>

**23:00**　Claude Code 从 node 升级成二进制以后，claude-trace 那些工具全失效了——再也看不到它到底给大模型发了什么。
我自己写了一个：ccglass。npm 装上、跑一行，它发给服务器的每个细节都摊在你眼前。 https://t.co/h4SPniy8Zi
<small>💬3 ♥43 🔁6</small>

> ↩️ 回复 @jianshuo：Claude Code 从 node 升级成二进制以后，claude-trace 那些工具全失效了——再也看不到它到底给大模型发了什么。 我自己写了一个：ccg…
**23:00**　零依赖，两行就跑起来：
npm install -g ccglass
ccglass
它会问你看哪个 client——Claude Code / Codex / Kimi。也可以直接 ccglass claude。
<small>💬1 ♥0 🔁0</small>

> ↩️ 回复 @jianshuo：零依赖，两行就跑起来： npm install -g ccglass ccglass 它会问你看哪个 client——Claude Code / Codex /…
**23:00**　system 标签：发给模型的系统提示词。第一句就是「You are Claude Code, Anthropic's official CLI for Claude.」，后面一长串行为约束，连 billing header 里的版本号都看得见。 https://t.co/0grvhjj8dX
<small>💬1 ♥0 🔁0</small>

> ↩️ 回复 @jianshuo：system 标签：发给模型的系统提示词。第一句就是「You are Claude Code, Anthropic's official CLI for Cla…
**23:00**　messages 标签：真正发过去的对话。你会看到一堆 &lt;system-reminder&gt;——这些是 Claude Code 自己塞进去的上下文，不是你打的字。 https://t.co/DZ6LcvbOcy
<small>💬1 ♥1 🔁0</small>

> ↩️ 回复 @jianshuo：messages 标签：真正发过去的对话。你会看到一堆 &lt;system-reminder&gt;——这些是 Claude Code 自己塞进去的上下文，不…
**23:00**　tools 标签：这一次普通请求就挂了 48 个工具。翻源码，光工具目录下就有 43 个，主体全是 Anthropic 写好的内置工具。 https://t.co/ezUhsqKrjK
<small>💬1 ♥0 🔁0</small>

> ↩️ 回复 @jianshuo：tools 标签：这一次普通请求就挂了 48 个工具。翻源码，光工具目录下就有 43 个，主体全是 Anthropic 写好的内置工具。 https://t.c…
**23:00**　response 标签：token 的账一清二楚。这次输入 2 个，缓存创建 53940 个，输出 116 个。
看得见，才谈得上理解。 https://t.co/SXEgxPzFtX
<small>💬1 ♥0 🔁0</small>

> ↩️ 回复 @jianshuo：response 标签：token 的账一清二楚。这次输入 2 个，缓存创建 53940 个，输出 116 个。 看得见，才谈得上理解。 https://t.c…
**23:00**　装上试试，看看你天天在用的工具，背地里都说了些什么。
开源：https://t.co/99thvxcoqh，欢迎翻源码、提 issue、一起来贡献。
<small>💬0 ♥5 🔁0</small>

## 周六 5月23日

**10:03**　看得见，才谈得上理解。我写了个 ccglass，npm 装上就能看到 Claude Code 背地里给大模型发了什么——系统提示词、48 个工具、token 账，全摊开。https://t.co/99thvxcoqh
<small>💬13 ♥171 🔁29</small>

> ↩️ 回复 @DashHuang：@jianshuo 我看你的 github，和我的节奏差不多呀，在 AI 的帮助下，老登程序员又能了！ https://t.co/wvWHc6727k
**10:10**　@DashHuang 对呀，原来其实就是体力不足，现在有了AI体力满血
<small>💬1 ♥5 🔁0</small>

**23:22**　过了五年， 才那么清晰的看到2021年，中国到底发生了什么。。。。一件接着一件，一条接着一条，没有一个季度停息过。 https://t.co/15liLOwnLO
<small>💬54 ♥466 🔁40</small>

> 🔁 引用 @jinchenma_ai：收藏一堆 AI 工具，其实是一种伪勤奋。 很多人的桌面上装了十几个 AI 工具，每个都「听说很强」。但真正每天在用的，可能就两三个。 工具多不等于效率高。恰恰相…
**23:24**　好多人都在问我 Claude Code和Codex到底哪个更强？似乎这是关心AI的人的必问题。我一直说，我不知道。我不是自媒体行业的，工具性能测试不是我的工作。我只用Claude Code，把所有的细节都用清楚，虽然我不能保证它是最好的工具。 https://t.co/FjWcEfNKe8
<small>💬4 ♥3 🔁0</small>

## 周日 5月24日

> 🔁 引用 @jinchenma_ai：@jianshuo 没那么复杂，对我来说，哪个有额度用哪个😂
**00:02**　我肯定还是要保持Claude Code满额 https://t.co/L1lFMULIHK
<small>💬0 ♥0 🔁0</small>

**00:04**　写代码的 agent 越来越聪明，也越来越像黑箱。ccglass 就是想给这个黑箱开一扇玻璃窗——现在能看清它每一步是怎么动的了。

0.3.0 新增：flow 时间线（看它怎么挑工具、跑、再喂回模型）、请求全文导出、agent 还能查自己。

https://t.co/99thvxcoqh
<small>💬0 ♥52 🔁6</small>

> 🔁 引用 @Fenng：沧海桑田之感。 https://t.co/EIIVPEcASs
**00:33**　2020年11月 — 蚂蚁集团上市叫停
2021年4月 — 阿里反垄断罚款182.28亿元
2021年6-12月 — 滴滴上市、App下架、退市
2021年7月 — 教培"双减"
2021年8月 — 游戏防沉迷新规
2021年10月 — 美团反垄断罚款34.42亿元
2021年12月 — HFCAA落地与"预摘牌名单"

2021年是个拐点 https://t.co/4Ku4iCtHw3
<small>💬2 ♥24 🔁1</small>

> 🔁 引用 @sgsg0507：@jianshuo 跟claude trace有啥区别
**13:51**　Claude Trace 新版本claude code 没法用了，这个可以用 https://t.co/8FHkJ4ofcu
<small>💬0 ♥1 🔁0</small>

> ↩️ 回复 @BeauJohnson89：coding agents need glass boxes now jianshuo/ccglass &gt; 111 stars on github &gt…
**16:52**　@BeauJohnson89 Thanks for picking it up. Yes. It started just to solve my own needs
<small>💬0 ♥0 🔁0</small>

> 🔁 引用 @stometaverse：@jianshuo ccglass 这个工具思路很好。能看见 Claude Code 发了什么 system prompt、tool schema、token …
**16:53**　的确任何东西如果有可能，从黑盒变成白盒都有价值 https://t.co/6lgVRwhMpE
<small>💬0 ♥3 🔁0</small>

> 🔁 引用 @mranti：@wong2__ 我刚来北京的时候，看到电梯工这个工种，那种震惊，难以言表：他们唯一的工作就是按电梯楼层按钮！
**17:38**　现在北京每一辆公交车上都有一个安全员，他们的工作比电梯工还少 - 他们只负责坐车 https://t.co/d6QecpvQQQ
<small>💬1 ♥3 🔁0</small>

**18:05**　大家都算错了一笔账：需求不变，除以提高的效率，得出需要更少的人。可历史上每一次都反过来——煤更高效了，用量涨了十几倍；程序员从五十万涨到八百万。被 AI 冲击的行业，才是该冲进去的行业。
<small>💬2 ♥20 🔁0</small>
