# VoiceDrop / jianshuo.dev Release Notes

**2026-07-14 ~ 2026-07-28 · 共 111 条上线记录**

## 主题总览

| # | 主题 | 代表性成果 |
|---|------|-----------|
| 1 | 提示词分享 → 市场（约 30 条） | MCP 分享 6 工具；魔法数字 4 位口播兑换；borrowed 溯源转发——未改正文返回原码、奖励归原作者；市场物化缓存 3–5s → 一次读取 |
| 2 | 出图 XMP 溯源（约 11 条） | paint 出图嵌 XMP（PNG iTXt / JPEG APP1）；口播分享码穿透到图片文件；防伪造校验 |
| 3 | 邀请与归因（约 15 条） | 邀请好友铸码 + 落地页 + claim；归因三修；PostHog 漏斗打点；访客 IP 后台；微信内 iOS 直跳 App Store |
| 4 | 存储迁移 D1（6 条） | P1–P3 全量迁 D1 voicedrop-core；列表一条 SELECT 直出；国内动态读走就近副本 |
| 5 | 国内速度 / EdgeOne（6 条） | voicedrop.cn 迁 EdgeOne；照片 302 直连（跨境 60KB/s 卡死 → 1.6s 全图）；照片缓存 1 天 → 1 年 |
| 6 | 语音编辑提速与质量（约 12 条） | put_article 8–22s → 亚秒；乐观回执压到网络往返级；锚点漂移自愈；写后校验（haiku 质检员） |
| 7 | ASR 热词（4 条） | 41 个请求级热词，批量 + 流式全吃，无需发版；汉字数字分享码可兑换 |
| 8 | 苹果订阅 IAP（4 条） | ¥19.9/月每月自动入账 200 算力；档位表；R2 零部署售卖开关 |
| 9 | 运维 / 后台 / 杂项（约 15 条） | OpenAI 额度耗尽 APNs 报警；4xx 报警风暴根治；admin 白名单准入；sitemap；MCP 调试器 /a/mcp |

---

## 逐日明细（新→旧）

### 2026-07-28（周二，2 条）

- log(miner): ASR 完成日志加 asr_dur_ms（火山检测的音频实际时长）
- feat(invite): 微信内去掉下载蒙层——iOS apps.apple.com 白名单直跳 App Store

### 2026-07-25（周六，6 条）

- fix(lib): writeArticleDoc 对 current 一侧同样清洗顶层字段 + 未迁移 doc 先迁移——堵直写引入的 schema 泄漏
- perf(agent): 乐观回执 + 瘦身写入——「正在生成」压到网络往返级
- fix(agent): 图片锚点漂移自愈 + 出图回复文案微调
- fix(agent): 连接快照 loadDoc 失败重试一次并打日志——null article 快照会消掉任务芯片却不更新正文
- perf(agent): 文章写入直连 article-store 库，砍掉 HTTP→Pages 绕行（put_article 8–22s → 亚秒）
- perf(agent+paint): 编辑 DO 钉 wnam + 模型配置缓存 + paint 输入图异步下载——治「fast path 也要十几秒」

### 2026-07-24（周五，11 条）

- perf(agent): 语音编辑提速三件套——长按图片 prompt 直通出图、photo 工具短路、写后校验只验高风险编辑
- fix(admin): llm/mine 日志日期列表跟 cursor 翻页——R2 delimited list 按扫描 key 数截断，日志攒多后新日期滚不出来（llm 页停在 07-13 的根因）
- remove(prompts): 系统缺省「合影照片」组删掉「电影感调色」「日系动画电影」两个动作
- remove(style): 下线多风格对比——miner 只按 head 文风挖单篇，/style API 不再读写 profile.styles
- fix(style): undo 后再写不再截断未来版本——整链保留，新版本接链尾
- feat(agent): 编辑 loop 写后校验（haiku 质检员）+ 长按菜单提示词开放给语音（use_my_prompt）
- feat(a): VoiceDrop 文章阅读数据报告页（reco engagement 近一月）
- feat(voicedrop-cn): route /agent and /reco through EdgeOne
- feat(voicedrop): 系统模板新增「合影照片」缺省组——AE209A 整组 6 个动作收编
- refactor(mcp): login tool splits code/verify_code/pairing, no more overloaded code field
- feat(a): add MCP visual debugger at /a/mcp

### 2026-07-22（周三，15 条）

- chore(voicedrop): nightly English mirror sync
- feat(voicedrop): Android 下载全线切应用宝，iOS/Android 下载并列
- fix(voicedrop): LibraryAgent queue 表补 anchor/item_id 列迁移——修长按语音指令卡死
- fix(voicedrop): 溯源转发 code-review 9 项修复
- feat(voicedrop): prompt-market 候选排除 borrowed 行（同码不重复展示）
- feat(voicedrop): borrowed 条目关分享只删自己索引，绝不碰原作者分享
- feat(voicedrop): 导入件再分享溯源转发——未改正文返回原码，奖励归原作者
- feat(voicedrop): effectiveLeaf 透传 importedFrom（写穿副本不带）
- feat(voicedrop): core-db prompt_shares 读写带 borrowed + coreDeletePromptShare
- feat(voicedrop): D1 migration 0004 — prompt_shares.borrowed + code 唯一索引改 partial
- fix(voicedrop): 落地页总守卫下限降到 4 字符，放行 4–5 位魔法数字
- feat(voicedrop): 魔法数字 4 位起步、占满自动升位
- fix(voicedrop): 根治 files/photo 4xx 报警风暴——畸形封面 key 拦截 + photo 404 静音
- feat(voicedrop): 提示词退出社区 feed + /agent/prompt-market 市场端点
- a/: add Cloudflare 增长引擎 + Zero Trust 科普两份报告页

### 2026-07-23（周四，1 条）

- perf(voicedrop): 提示词市场物化缓存——打开从 3-5s 降到一次 R2 读

### 2026-07-21（周二，7 条）

- chore(voicedrop): nightly English mirror sync
- feat(voicedrop): sitemap.xml(动态,含公开社区帖) + robots.txt
- fix(voicedrop/admin): 准入接受 anon_ 访问令牌（app 默认凭证），不只签名 session
- refactor(voicedrop/admin): 白名单按不可篡改的 scope/ID 码匹配，去掉可冒充的名字匹配
- feat(voicedrop/admin): 后台准入从 FILES_TOKEN 改成用户白名单
- feat(realtime): OpenAI 额度耗尽(insufficient_quota)时 APNs 报警管理员 + iOS 停重连风暴
- feat(voicedrop): 社区分享每日限额 20→200

### 2026-07-20（周一，12 条）

- perf(voicedrop): D1 read replication——国内动态读走就近副本
- docs(a): 收录 VoiceDrop 存储排查·D1 迁移页到 /a/，更新索引卡片
- feat(voicedrop): 存储迁移 P3——身份/档案/push token/举报迁 D1
- feat(voicedrop): 存储迁移 P2——文章/录音索引迁 D1，列表接口一条 SELECT 直出
- feat(voicedrop): 存储迁移 P1——refhits/invites/prompt-shares/importCount 迁 D1 voicedrop-core
- feat(agent): 流式 ASR 热词——/agent/asr 代理拦截 full client request 帧注入 corpus.context，实时预览+口述改稿同吃热词，无需 App 发版
- feat(agent): ASR 请求级热词——auc submit 带 corpus.context(题图/图一~图二十/分享码等41词)，同音错字在转写层就地消灭
- feat(agent): 分享码模型侧推断解析 use_shared_prompt——ASR 汉字数字(七七六六四四3)可兑换，码长不写死(≥3位)；EDIT_SYSTEM 补同音错字目标推断+复述规则
- perf(files): 照片 200 缓存 1 天 → 1 年 immutable(key 写入后不变;404 no-store 不动)
- docs(voicedrop-cn-edgeone): 证书终态=eofreecert 已部署;记录 apex CNAME 扁平化误报
- feat(infra): voicedrop.cn 迁移 EdgeOne 完成——边缘函数替代 VPS Caddy,照片走国内边缘缓存
- Add EdgeOne ownership verification file for voicedrop.cn

### 2026-07-18（周六，5 条）

- chore(voicedrop): nightly English mirror sync
- fix(paint-size): 补 gpt-image-2 总像素下限——竖图 9:16 缩成 576x1024 不足 655360 被 paint 整单拒，现等比放大到达标（竖版照片改风格必失败的根因）
- fix(voicedrop-cn): 照片/封面 302 直连 jianshuo.dev——盒子跨境仅 ~60KB/s，分享页图片全卡死；已上线验证 1.6s 取全图
- feat(files-api): POST wechat-validate——保存前经 relay 从白名单 IP 真拿一次 token，微信侧 errcode 原样透传给 App
- report(a): VoiceDrop 访客周报 2026-07-14~18（PostHog 首周数据）

### 2026-07-19（周日，16 条）

- refactor(agent): 删文字反查换 item_id 精确解析——payload/queue/ctx 全链穿透 item_id，magicForItem 走 byItem+importedFrom
- feat(agent): 长按菜单调指令出图也带魔法数字——指令文本反查自己的活跃分享码进 XMP
- fix(agent): 照片 key 不再用绝对毫秒时间戳——改图保留原图偏移前缀只换随机尾，生成图用会话目录+秒偏移
- feat(agent): 口播分享码穿透到出图 XMP——resolveSharedPromptBlock 返回 {block,magic}，ctx.sharedMagic 下行
- perf(prompts): 保存不再等分享副本同步——rekey+同步挪进 ctx.waitUntil 后台
- feat(agent): paint XMP 溯源调用方接线——VoiceDrop 关 prompt 只标来源，prompt-lab 带指令 id/魔法数字
- fix(paint): harden xmp_meta key validation against spoofed provenance
- feat(paint): worker 出图后回调前嵌入 XMP 溯源
- feat(paint): POST /api/jobs 收 xmp_prompt / xmp_meta（校验 + 入库）
- feat(paint): embedXmp — PNG iTXt / JPEG APP1 原子插块
- feat(paint): buildXmp 拼 XMP 溯源包
- feat(usage): 新用户注册赠送 500 → 200 算力
- docs: paint XMP 溯源实现计划
- feat(prompt-share): 分享提示词带分组落位——副本记 groupPath，收下进同名组/自动建组，标题「分组｜名字」
- docs: paint 出图自带 XMP 溯源 design spec
- feat(style): 文风版本保留上限 10 → 20

### 2026-07-17（周五，9 条）

- feat(admin): 访客 IP 并入 /voicedrop/admin 后台——新页 refhits.html + master token 鉴权
- fix(referral): beacon 只在反代页注入——直连页不再一次访问记两条指纹
- feat(analytics): 分享页访问打点——文章/社区/提示词三类页发「分享页访问」事件
- feat(referral): 访客 IP 一览调试页 GET /agent/referral/refhits?key=…
- debug(referral): 指纹临时改明文 IP（DEBUG_PLAINTEXT_IP 开关）+ test owner 不写指纹
- feat(iap): 售卖开关——R2 config/iap.json {"enabled":true} 零部署开闸，默认关
- feat(iap): 订阅产品 ID 带价格 + 档位表——monthly_19_9，以后加档只加一行
- chore(test): fakes 注释同步 0004 迁移
- feat(iap): 苹果订阅 P3 服务端——¥19.9/月每月自动入账 200 算力桶

### 2026-07-16（周四，18 条）

- feat(prompts): 「收下这条提示词」幂等——同码重复导入不再重复添加
- 提示词分享页「收进工具箱」改 universal link：跨域 https 链接替代 voicedrop:// scheme
- fix(referral): 打点真实 IP 改走 X-Forwarded-For 首段——X-Real-IP 被 CF 边缘覆写不可用
- fix(referral): 落地页打点 distinct_id 用 X-Real-IP 真实访客 IP——PostHog 里不再「全是同一个人」
- feat(auth): 绑过实名的匿名 scope 获社区写权限——MCP 配对 token 可分享/取消分享/投币
- feat(invite): 邀请落地页分享卡片带 App logo（og:image/image_src → icon-512.png）
- fix(referral): 归因三修——第一方 beacon 复活 IP 层、剪贴板 execCommand 兜底+微信蒙层、邀请人到账推送
- chore(agent): POSTHOG_API_KEY 进 worker vars（phc_ 可公开客户端 key，用户授权 2026-07-16）
- feat(referral): 漏斗打点进 PostHog——落地页访问/下载点击/claim 结果分布
- feat(share): prompt 分享页加「一键收进我的工具箱」按钮
- fix(share): prompt 社区帖公开页 404——kind=prompt 无 articleKey，原地渲染指令页
- fix(edit): 锚点 image key 校验做两代照片标记归一——legacy [[photo:N]] 数字 token 经 doc.photos 解析成相对 key，老文章长按图片不再被静默丢弃——锚点 T1 review fix
- feat(edit): 锚点协议服务端——anchor 透传/校验/漂移自愈/上下文注入——锚点 T1
- feat(referral): 邀请好友——/agent/referral/link 铸码 + voicedrop.cn/i/<码> 落地页 + claim 认邀请码
- fix(community): 提示词帖两洞——[[photo]] 占位符不再抠成假题图；投币支持 prompt 帖
- perf(prompt-share): 黑名单读并进并行组 + 首铸跳过 importCount 保护读——关键路径 ~3 个来回
- perf(prompt-share): 开分享从 ~15 个串行存储操作压到 ~6——并行前段读 + 发帖挪 waitUntil
- feat(mint): 投喂到账给作者发 APNs 推送，点开进算力账单

### 2026-07-15（周三，8 条）

- fix(community): 提示词帖同死补漏——举报下架/销号连码删 + 举报列表摘要 + 自愈防误删
- docs(mcp): share_prompt/unshare_prompt 描述跟上自动发社区帖语义——Task 6
- feat(community): get 合成提示词帖形状 + unshare 帖码同死 + reconcile 收编——Task 5
- feat(agent): 开分享=铸码+发社区帖，关分享=帖码同死；登录门槛+审核——Task 4
- feat(agent): 提示词社区帖发布/撤回帮手 + RECO_DB binding——Task 3
- feat(community): 展示索引与 list 认 kind 列——提示词社区帖 Task 2
- feat(reco): community_posts 加 kind 列，feed 透传——提示词社区帖 Task 1
- feat(mcp): 提示词分享 6 工具——list/share/unshare/status/preview/import

### 2026-07-14（周二，1 条）

- chore(voicedrop): nightly English mirror sync

