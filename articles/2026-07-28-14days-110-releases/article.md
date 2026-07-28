过去 14 天，我的 VoiceDrop 上线了 110 次。

这个数字不是感觉，是 `git log` 数出来的：从 7 月 14 日到 7 月 28 日，110 条提交，每一条都真的部署到了线上。平均每天 8 次，周末也没停。

干活的不是一个团队，是我一个人，加上 Claude。

我把这 110 条 release note 从头到尾翻了一遍，想回答一个问题：这两周到底做成了什么？翻完发现，可以归成四件事。

**第一件事：让每一条提示词，都记得自己的作者是谁。**

VoiceDrop 是一个用语音写文章的 App。里面有一种东西叫提示词——比如「把这张图改成手绘解释风」，一条调好的指令。

这两周，提示词从「自己用」长成了一个小市场。三条 release note 把路铺完了：

- 7 月 22 日：「魔法数字 4 位起步、占满自动升位」。每条分享出去的提示词有一个 4 位数字的码，对着手机念出来就能兑换，像口令红包。
- 7 月 22 日：「导入件再分享溯源转发——未改正文返回原码，奖励归原作者」。你收下我的提示词，再转给别人，码还是我的，奖励也是我的。
- 7 月 19 日：「worker 出图后回调前嵌入 XMP 溯源」。AI 生成的每张图，用了谁的提示词，直接写进图片文件内部。图走到哪，作者跟到哪。

为什么要费这个劲？因为一个市场能不能长起来，取决于创作者的东西会不会被白拿。<span style="color:#ff0000;">链路记住作者，分享才有动力。</span>

**第二件事：把国内用户的等待，从卡死降到 1.6 秒。**

有人反馈：分享页的图片一直转圈。查下来不是代码慢，是光缆慢——跨境线路只有 60KB/s。

解法是三层，一层比一层深：

- 7 月 18 日：「照片/封面 302 直连——已上线验证 1.6 秒取全图」。先止血。
- 7 月 20 日：「voicedrop.cn 迁移 EdgeOne 完成——边缘函数替代 VPS 反代，照片走国内边缘缓存」。图片不再过境。
- 7 月 20 日：「D1 read replication——国内动态读走就近副本」。连数据库的读，都挪到离用户近的地方。

**第三件事：把「正在生成」从十几秒压到一秒以内。**

用语音改文章，最难受的是等。你说完「把第三段改简洁」，屏幕转圈十几秒，人就走神了。

7 月 25 日一天连发三条，把这件事了结了：

- 「文章写入直连数据库——单次写入从 8–22 秒到亚秒」。原来每次保存要绕一圈 HTTP，现在直着走。
- 「编辑服务钉在固定机房 + 模型配置缓存」——治「快路径也要十几秒」。
- 「乐观回执——『正在生成』压到网络往返级」。先把号牌塞你手里，菜在后厨接着做。

快了会不会错？前一天（7 月 24 日）先上了「写后校验：haiku 质检员」——每次改动背后，还有一个小模型在把关。

**第四件事：同音错字，在转写层就地消灭。**

「题图」被转成「提图」，「分享码」变成「分想马」。以前的思路是转写完再修，这次直接往上游走了一步。

7 月 20 日：「ASR 请求级热词——带 41 个热词（题图/图一到图二十/分享码等），同音错字在转写层就地消灭」。同一天，流式转写也吃上了热词，而且「无需 App 发版」。

顺手还支持了汉字数字：你念「七七六六四四」，他知道那是一个分享码，不是四个字。

这四件之外，还有一串小的，每条都有对应的 release note：

- 7 月 17 日：苹果订阅上线，19.9 元一个月，每月自动入账 200 算力。
- 7 月 16 日：邀请好友——铸码、落地页、到账给邀请人推送。
- 7 月 21 日：OpenAI 额度耗尽时，直接推送报警到我手机，不用等用户来报。
- 7 月 23 日：提示词市场打开速度，从 3–5 秒降到一次读取。

最后说本质。

14 天 110 次上线，不是因为我打字变快了，是<span style="color:#ff0000;">发布的成本变了</span>。以前发布一次要排期、测试、走流程；现在一个想法从冒出来到用户手上，平均不到两个小时。

成本变了，节奏就变了；节奏变了，做产品的方式就变了——从憋一个大招，变成每天往前挪八小步。

<span style="color:#ff0000;">发布的节奏，就是产品的心跳。</span>

心跳快的产品，不一定赢；心跳停的产品，一定死。

我们需要做的，就是让它一直跳下去。

![](./illustration.png)

<!--RECENT_ARTICLES_START-->
<section style="margin-top:28px;padding-top:16px;border-top:1px solid #e5e5e5;"><strong style="color:#ff0000;">扩展阅读</strong><br><a class="normal_text_link mp_article_text_link" target="_blank" style="" href="https://mp.weixin.qq.com/s/y7kQ0J46lDjXO3Ojn5L73g" textvalue="效率越高，需求越井喷" data-itemshowtype="0" linktype="text" data-linktype="2">效率越高，需求越井喷</a><br><a class="normal_text_link mp_article_text_link" target="_blank" style="" href="https://mp.weixin.qq.com/s/WHDieFP7zc6iUS8nWVxcwg" textvalue="把 LLM 当编译器，把 Skill 当 App" data-itemshowtype="0" linktype="text" data-linktype="2">把 LLM 当编译器，把 Skill 当 App</a><br><a class="normal_text_link mp_article_text_link" target="_blank" style="" href="https://mp.weixin.qq.com/s/IdRiOB79uO2rvSp9166Dnw" textvalue="用 Claude Code，你以为说了一个 Hello？不是，你发过去一本三国演义" data-itemshowtype="0" linktype="text" data-linktype="2">用 Claude Code，你以为说了一个 Hello？不是，你发过去一本三国演义</a><br><a class="normal_text_link mp_article_text_link" target="_blank" style="" href="https://mp.weixin.qq.com/s/-HK2ymNH3bhun-zQ65cmBQ" textvalue="改指令，不要改产物" data-itemshowtype="0" linktype="text" data-linktype="2">改指令，不要改产物</a><br><a class="normal_text_link mp_article_text_link" target="_blank" style="" href="https://mp.weixin.qq.com/s/-7u-Sx6yiIXWMSFCB62FTA" textvalue="我写了个 ccglass，看看 Claude Code 向大模型发了什么" data-itemshowtype="0" linktype="text" data-linktype="2">我写了个 ccglass，看看 Claude Code 向大模型发了什么</a></section>
<!--RECENT_ARTICLES_END-->
