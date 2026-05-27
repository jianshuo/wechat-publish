# 我写了个 ccglass，看看 Claude Code 向大模型发了什么

我做了个工具，叫 ccglass，能直接看到 Claude Code 发给大语言模型的所有后台信息。

这事原来 claude-trace 之类的工具能干。但 Claude Code 从 node 升级成二进制文件以后，它们**全都用不了了**。

只好自己写一个。

昨天晚上做出来，今天包成了一个 node 包发到了 npm 上。零依赖，装上、运行两行：

<section style="background:#f6f8fa;border-radius:6px;padding:14px 16px;overflow-x:auto;font-family:Menlo,Consolas,monospace;font-size:14px;line-height:1.8;color:#24292e;">npm install -g ccglass<br>ccglass</section>

![](http://mmbiz.qpic.cn/mmbiz_png/x701icxIMoQMjiaw9ib1QxNGvsMBD0456CHiakgmZJKNDjKDnIP6DUY0Cv9WKCuiaCskjE2GmC320LAgPfUx9ey0eiaPicNLhFTcSSGy6o6RYLvLFU/0?wx_fmt=png)

说起来我基本没怎么上传过 npm 包，这算是最近几年第一个，过程极度丝滑。

运行后它会问你想看哪个 client——Claude Code、Codex、还是 Kimi。选 Claude，就能看到它发给服务器的**每一个细节**。

也可以直接点名：

<section style="background:#f6f8fa;border-radius:6px;padding:14px 16px;overflow-x:auto;font-family:Menlo,Consolas,monospace;font-size:14px;line-height:1.8;color:#24292e;">ccglass claude<br>ccglass codex<br>ccglass kimi</section>

打开之后是这样的。左边是一次次请求，右边分了 overview、system、messages、tools、response、headers 几个标签。

system 标签里，是发给模型的系统提示词。第一句就是「You are Claude Code, Anthropic's official CLI for Claude.」，后面跟着一长串行为约束，连 billing header 里的版本号都看得见。

![](http://mmbiz.qpic.cn/mmbiz_png/x701icxIMoQPWX67gvVo12BuONBJq8l0fBrttNsw4YlPY7YEdlcc6h1fgwaMicOylRzfbXVIoKoX6ZPt3LNdaJKW64SiacKHTbkdcDd9wWjtdo/0?wx_fmt=png)

messages 标签里，是真正发过去的对话。你会看到一堆 `<system-reminder>`——这些是 Claude Code 自己塞进去的上下文，不是我打的字。

![](http://mmbiz.qpic.cn/sz_mmbiz_png/x701icxIMoQPHkiaYf9GkQWpoSP3JpZaniccYWWTicKLIP3owe1anvCVjwpOdO0jAkS8FZuthiaarnknpWFw4dFbWJQq8KJoF4uImQKcYKtNSJr0/0?wx_fmt=png)

tools 标签里，列着这一次请求带上的所有工具定义。一次普通对话就挂了 48 个工具。翻源代码，光工具目录下面就有 43 个——主体其实都是 Anthropic 自己写好的内置工具。

![](http://mmbiz.qpic.cn/sz_mmbiz_png/x701icxIMoQM8jCWFyQ2knEK2pvAbE2nIeM39Glh7YfRK8Bhic74qcScSPWwgM3PThqNTm7ric0ribOcuEX10wQdLwLo3GYZdubfqTJuiaYU9wGs/0?wx_fmt=png)

response 标签里，能看到 token 的账：这次输入 2 个，缓存创建了 53940 个，输出 116 个。

![](http://mmbiz.qpic.cn/mmbiz_png/x701icxIMoQOW8MK5f4IDT4UDE7usx33frUNODa2AEBSfzMR6ICXOjPWNGP97H7fia9gao5Ar93XK9BJtMXEEHA0tPlibBgriazEhMmpicOSxZw4/0?wx_fmt=png)

**看得见，才谈得上理解。**大家可以装上试试，看看自己每天在用的工具，背地里都说了些什么。

代码全部开源在 github.com/jianshuo/ccglass，欢迎去翻源码、提 issue，也欢迎一起来贡献。
