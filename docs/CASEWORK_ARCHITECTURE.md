# 共享处置模块架构

## 数据与入口

```text
POST /api/workbench/cases                 scan_id + row_id → 幂等事件
GET  /api/workbench/cases                 授权事件、过程统计、报告JSON
GET  /api/workbench/cases/{id}            快照、表单、历史、复查及通知
GET  /api/workbench/casework/config       当前身份、模板、配置是否就绪
POST /api/workbench/cases/{id}/commands   version + request_id + 操作 → 统一状态机
POST /api/workbench/cases/{id}/rechecks   当前用户真实数据权限 → 复查快照
POST /api/workbench/cases/{id}/notify     测试白名单目标 → 持久化发送队列
POST /api/integrations/feishu/card-callback  机器签名 → 映射身份 → 同一个状态机
```

`wbFinish` 在扫描缓存成功写盘后将真实命中写入共享台账。旧个人扫描和标记不删除；旧个人 actions 接口不写共享事件。新UI的可编辑处置入口全部走共享状态机，原历史标记只读展示。

单实例 SQLite 文件 `AIME_PLUGIN_DATA_DIR/tap_casework.db`，和旧扫描缓存独立：

- `tap_cases`：稳定 id、version、完整事件JSON，含初始 row、window、rule、负责人、模板版本、结构化方案、历史、真实复查。
- `tap_commands`：case_id + request_id 唯一；指纹校验 actor/source/payload，保证同请求幂等。
- `tap_outbox`：发送或更新任务、目标、状态、attempts、next_at、message_id、错误与时间。

处置保存、审计追加、命令去重记录、已有消息的更新任务，在同一个 SQLite 事务内提交；数据库保存失败不提示处理成功。并发使用 version 条件更新和事务，旧卡片/旧网页表单返回冲突。

## 权限

原 AIME JWT 校验保留。运营列表显式配置；负责人、创建者、指定复核人可见，普通用户看不到别人的台账。创建者不因创建记录自动获得关闭权。负责人及运营可处置，指定复核人可复核，审批/分派/重开由运营执行；提交人与关闭复核人分离。

飞书操作者 open_id 经配置映射到相同 AIME username，再按相同权限检查。回调只认可此应用发送并记录过的 message_id。Web 和飞书均不能靠上传 actor 字段伪造操作者。

## 通知与回调

HTTP 新版加密回调：SHA256(timestamp + nonce + EncryptKey + 原始body)，5分钟时钟窗口，AES-256-CBC解密，Verification Token、App ID 与可选 tenant_key 检查。加密URL验证返回 challenge。

回调不查询风神，不调用外部消息API。短事务保存后返回 Toast；持久化队列异步 PATCH 原卡片。机器路由无浏览器JWT依赖，但仍需AIME外层网关允许该路径通过。

后台进程每2秒处理一个待发任务，网络有超时，Token缓存与过期刷新；任务退避重试，重启恢复未完成任务。发送与更新都按当前事件版本生成卡片，发送过程中发生变更则补更新任务。实际发送与SQLite之间无法跨平台原子提交，使用稳定 uuid 缓解重复投递；不宣称无限期exactly-once。

## 复查与报告

复查默认人工选择独立窗口，当前点击者 JWT 查原ET/THT接口，保存成功/失败和NULL值，保留原指标快照。风险恢复关闭必须满足完整指标、原规则不再触发、窗口晚于原报警窗口且不早于处置日、另一人复核。人工例外关闭分开归类。

过程报告计事件、动作完成、待复核、关闭原因、通知已发送、逾期；风险恢复仅计独立复查通过并关闭。不把本期QTD下降、沟通完成、message_id或网页点击当成风险恢复/消息已读。

## 后续扩展合同

Quota 使用独立workflow，但真实事件生成器待接入；ST真实数据仍待接入。未来可把共享台账仓储迁移到统一云数据库，把outbox迁移到队列；状态机与前端commands合同无需改变。定时复查需先落实服务端数据访问身份，不能通过永久保存个人JWT实现。通知收件人政策和跨窗口风险周期合并需要业务确认。
