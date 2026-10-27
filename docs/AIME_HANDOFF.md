# 给 AIME 的更新指令 · 预警处置闭环版 2026-10-19

在同一个 App `app_e5d1388d65ef1b49` 安装本包，保留服务端数据目录、已验证的风神身份和数据源配置。此包承接四页构建修复版本，不要回退 ET/THT 取数修复。

1. 同时更新前端与 Go 后端并重启；新增共享事件/飞书接口不支持只替换前端。正式产物为 app/dist 和 app/server-go/bin/server。平台标准重建也必须包含本包新增Go文件，避免旧 .aime_build 二进制覆盖。
2. 按 docs/FEISHU_PILOT_GUIDE.md 创建企业自建 Bot、配置凭证安全注入、两人 username/open_id 和测试群 chat_id。配置入口为 config/casework.json；默认 disabled，准备完成后改 test。
3. 为唯一机器路由 /api/integrations/feishu/card-callback 确认实际HTTPS域名、网关放行及 X-Lark-* 请求头/原始body透传；该接口独立验证加密签名及Token。其他接口继续走原AIME鉴权。保存新版 card.action.trigger HTTP 加密回调的 challenge 成功，再测卡片。
4. 风神扫描仍按个人权限，处置台账改为同一实例的共享SQLite（按人员权限过滤），保存在原持久化目录下 tap_casework.db；不要用临时构建目录，不要复制真实数据库进入源码包。
5. 真实ET/THT完成扫描后，绝对值命中加入共享台账；仅选择1个客户测试显式发送，确认真实message_id、卡片内接单/表单保存、工作台同步、原卡片更新及审计一致性。群成员不自动拥有处置权。
6. 业务模板为pilot待确认；客户和Quota分开。Quota真实事件生成、ST数据、自动复查、自动群发、逾期升级通知尚未启用。不要把按钮已渲染或队列pending等同于真实消息成功。
7. 复核关闭与动作完成分开。真实风险恢复需要独立窗口完整数据、无命中、另一账号复核；人工例外关闭分开统计，移除申请不自动执行TAP变更。
8. 严格执行指引中的12项验收。若机器回调被外层SSO阻挡，明确解决网关可达性，不能退化成跳转链接后声称Bot内处理完成。

本地验证见 docs/VALIDATION.md；实际公司SSO、风神覆盖、Bot权限及网关可达性需在AIME实查。Secret只通过安全配置输入，不输出到日志或前端。
