# 本次数据接入说明（2026-10-19）

本次只扩展页面和读取保存记录的能力，ET/THT的实际数据源、字段、筛选、鉴权与规则，以此包 `config/data_sources.yaml`、`config/alert_workbench.json` 和原查询适配器为准；与用户10月19日上传版本保持一致。

- ET名单、THT工单、ET/THT指标的RID及字段合同由既有配置提供。请勿从此前10月16日的文档恢复旧 submission_detail RID。
- ET按Account ID，THT按Advertiser ID。列表、详情、数据卡片均使用对应对象ID；同窗口客户指标不得相加/平均伪造项目整体指标。
- 现有扫描入口：POST /api/monitoring/risk-scans；进度/结果：GET /api/monitoring/risk-scans/{id}。原 workbench 别名与处理记录接口继续保留。
- 新增 GET /api/workbench/history：受原鉴权保护，返回 data.scans（当前用户最近10次保存扫描）、data.actions（关联记录）、scope=current_user_recent_scans、limit=10。不额外发起风神取数。
- GET /api/workbench/config 只额外返回 quota_baseline，原有字段和来源保留。该基线来自 config/quota_baseline.json，status=reference_pending_period_confirmation；没有用量值，不参与虚构配额告警。
- 总览只合并与所选指标日期、提报日期及区域完全匹配的各项目最近扫描；分析按Alert ID去重，在保留记录内确定首次发现时间。
- 处理记录继续使用原接口和原JSON文件，不改变存储格式。历史/操作记录按当前用户隔离，不能作为团队全量报表。
- 周度趋势需要周粒度查询；复测改善需要真实复测与执行记录；Quota使用量需要完整APPROVE工单与版本化有效配额。未接入时各页面明确显示待接入，不使用历史演示数据补齐。
