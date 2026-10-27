# TAP Governance Workbench · 预警处置闭环测试版 · 2026-10-19

本包在四页构建修复版基础上，增加共享风险事件、结构化处置、复核关闭及飞书双向接口。保留现有 AIME 应用身份、ET/THT 源配置、绝对值规则和查询适配器。安装到同一个 App `app_e5d1388d65ef1b49`，保留已有持久化数据目录。

## 从这里开始

- **配置与测试步骤**：`docs/FEISHU_PILOT_GUIDE.md`。包括创建自建应用 Bot、权限/发布、两人及群身份、8项服务端变量、加密机器回调、11步真实链路及12项验收。
- **部署指令**：`docs/AIME_HANDOFF.md`。
- **数据和接口架构**：`docs/CASEWORK_ARCHITECTURE.md`。
- **实际验证与边界**：`docs/VALIDATION.md`。

## 本次功能

1. ET/THT 扫描的真实绝对值命中进入 SQLite 共享台账，按角色访问；扫描缓存仍按原用户隔离。
2. 风险页增加共享收件箱；事件有核查与处置、复查与复核、分派与通知、操作记录四个独立页签。
3. 客户沟通整改、观察、跨团队核查、移除申请、无需处置各有必填项和流转。Quota 使用独立模板，真实 Quota 事件生成入口待接入。
4. 所有新处置均走带版本、幂等键和审计的统一服务。完成动作不直接确认风险恢复，关闭需另一账号复核；移除审批不直接改变 TAP 保护状态。
5. 飞书实际发送、原消息更新、重试、加密回调、操作者映射和卡片内处理均已实现。默认关闭真实发送；启用 test 模式后仅向显式配置的测试白名单目标点击发送。
6. 手动独立窗口查真实 ET/THT 指标、保存复查；过程报告、动作完成和真实复查恢复分别统计。

未启用自动群发、定时复查及逾期升级通知。ST 数据、真实 Quota 使用量、完整业务关闭标准仍待确认接入。本包不包含公司密钥、真实飞书消息或演示客户数据。

## 构建与安装

包含 React/Go 源码、前端产物、Linux amd64 服务二进制；沿用原 start.sh。必须同时更新后端和前端。如果 AIME 优先启动旧的 .aime_build/bin/server，应通过平台标准重建更新它；发布包不携带旧开发二进制。

```sh
TAP_BUILD_NODE_MODULES=/absolute/path/to/node_modules node tools/build_workbench.mjs
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -buildvcs=false -trimpath -ldflags='-s -w' -o app/server-go/bin/server ./app/server-go
go test -race ./app/server-go
cd app/frontend
npx tsc -p tsconfig.workbench.json
npx vitest run --config vitest.workbench.config.ts
```

上一版两处 TypeScript 测试兼容错误已保留修复。原 pnpm/typecheck/Vite 及内网SDK入口不绕过；本地不能下载内网SDK，不声称内网标准全量构建已通过。详见验证记录。
