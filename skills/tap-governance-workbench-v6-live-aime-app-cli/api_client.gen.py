# CODE GENERATED FROM app/api/api.yaml BY tools/gen_api.py — DO NOT EDIT
"""command / hook 调用本应用后端接口的 typed 封装（基于 utils.service_client）。

写操作（POST/PUT/PATCH/DELETE）成功后自动调用 notify_refresh，
通知已打开的前端页面刷新数据。前端自己调用 API 时不经过此层，不会触发多余刷新。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from utils.service_client import call_service, notify_refresh  # noqa: E402

def admin_sync_create(body=None, query=None) -> dict:
    """POST /api/admin/sync — 按数据源和运行时筛选触发同步"""
    result = call_service("/api/admin/sync", method="POST", body=body, query=query)
    notify_refresh("admin")
    return result


def governance_identity_diagnostics_list(query=None) -> dict:
    """GET /api/governance/identity-diagnostics — 获取工作台登录身份、风神短期凭证状态、网络状态与逐 Report 查询状态"""
    return call_service("/api/governance/identity-diagnostics", method="GET", query=query)


def governance_registry_list(query=None) -> dict:
    """GET /api/governance/registry — 获取数据源合同、粒度、Ready/Conditional/Blocked 状态、快照与质量诊断；S04仅名称补充，S09范围合同不足时保持conditional/unknown"""
    return call_service("/api/governance/registry", method="GET", query=query)


def governance_sync_status_list(query=None) -> dict:
    """GET /api/governance/sync-status — 获取最近同步运行状态"""
    return call_service("/api/governance/sync-status", method="GET", query=query)


def governance_tabs_by_tab_get(tab, query=None) -> dict:
    """GET /api/governance/tabs/{tab} — 获取五个治理 Tab 的标准卡片和图表数据"""
    return call_service(f"/api/governance/tabs/{tab}", method="GET", query=query)


def integrations_feishu_card_callback_create(body=None, query=None) -> dict:
    """POST /api/integrations/feishu/card-callback — 飞书新版加密卡片回调，独立签名和身份校验，不要求浏览器JWT"""
    result = call_service("/api/integrations/feishu/card-callback", method="POST", body=body, query=query)
    notify_refresh("integrations")
    return result


def integrations_feishu_config_status_list(query=None) -> dict:
    """GET /api/integrations/feishu/config-status — 管理员读取飞书 Bot 凭证配置状态（永不返回 Secret 或 Token）"""
    return call_service("/api/integrations/feishu/config-status", method="GET", query=query)


def integrations_feishu_credentials_create(body=None, query=None) -> dict:
    """POST /api/integrations/feishu/credentials — 管理员验证并原子保存飞书 Bot 凭证"""
    result = call_service("/api/integrations/feishu/credentials", method="POST", body=body, query=query)
    notify_refresh("integrations")
    return result


def integrations_feishu_test_message_create(body=None, query=None) -> dict:
    """POST /api/integrations/feishu/test-message — 管理员仅向后端测试白名单中的指定邮箱发送无客户信息纯文本测试消息"""
    result = call_service("/api/integrations/feishu/test-message", method="POST", body=body, query=query)
    notify_refresh("integrations")
    return result


def integrations_feishu_test_recipient_create(body=None, query=None) -> dict:
    """POST /api/integrations/feishu/test-recipient — 管理员按完整企业邮箱解析并保存唯一测试接收人，启用 test 模式"""
    result = call_service("/api/integrations/feishu/test-recipient", method="POST", body=body, query=query)
    notify_refresh("integrations")
    return result


def monitoring_et_current_create(body=None, query=None) -> dict:
    """POST /api/monitoring/et/current — 查询单个 ET Account 的权威 Account 粒度 Current P0 CCR/NFS/Revenue 真实业务数据"""
    result = call_service("/api/monitoring/et/current", method="POST", body=body, query=query)
    notify_refresh("monitoring")
    return result


def monitoring_risk_scans_create(body=None, query=None) -> dict:
    """POST /api/monitoring/risk-scans — 创建 ET/THT 高风险客户异步扫描"""
    result = call_service("/api/monitoring/risk-scans", method="POST", body=body, query=query)
    notify_refresh("monitoring")
    return result


def monitoring_risk_scans_by_id_get(id, query=None) -> dict:
    """GET /api/monitoring/risk-scans/{id} — 查询 ET/THT 高风险客户扫描进度与完整结果"""
    return call_service(f"/api/monitoring/risk-scans/{id}", method="GET", query=query)


def monitoring_risk_scans_by_id_resume_missing_create(id, body=None, query=None) -> dict:
    """POST /api/monitoring/risk-scans/{id}/resume-missing — 在既有 ET 扫描任务内按 checkpoint 连续补齐 not_queried/failed Current 指标，不重扫 membership"""
    result = call_service(f"/api/monitoring/risk-scans/{id}/resume-missing", method="POST", body=body, query=query)
    notify_refresh("monitoring")
    return result


def submissions_list(query=None) -> dict:
    """GET /api/submissions — 查询最近成功快照中的提报数据"""
    return call_service("/api/submissions", method="GET", query=query)


def submissions_quota_list(query=None) -> dict:
    """GET /api/submissions/quota — 按季度和时间窗聚合 ET、THT、ST 提报及 Quota 使用率"""
    return call_service("/api/submissions/quota", method="GET", query=query)


def submissions_st_snapshots_create(body=None, query=None) -> dict:
    """POST /api/submissions/st-snapshots — 使用当前用户 JWT 运行时读取 ST Q4/Q3 权威 Sheet，校验后持久化快照"""
    result = call_service("/api/submissions/st-snapshots", method="POST", body=body, query=query)
    notify_refresh("submissions")
    return result


def submissions_status_list(query=None) -> dict:
    """GET /api/submissions/status — 查询提报数据质量与快照状态"""
    return call_service("/api/submissions/status", method="GET", query=query)


def workbench_analytics_list(query=None) -> dict:
    """GET /api/workbench/analytics — 运营按共享事件台账查询治理分析"""
    return call_service("/api/workbench/analytics", method="GET", query=query)


def workbench_analytics_export_list(query=None) -> dict:
    """GET /api/workbench/analytics/export — 运营按同一筛选口径导出治理分析Excel"""
    return call_service("/api/workbench/analytics/export", method="GET", query=query)


def workbench_analytics_export_html_list(query=None) -> dict:
    """GET /api/workbench/analytics/export-html — 导出与当前筛选和数据版本一致的独立只读HTML治理报告"""
    return call_service("/api/workbench/analytics/export-html", method="GET", query=query)


def workbench_analytics_reports_create(body=None, query=None) -> dict:
    """POST /api/workbench/analytics/reports — 按当前真实统计与筛选生成不可变治理报告版本并保存到 Cloud DB"""
    result = call_service("/api/workbench/analytics/reports", method="POST", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_analytics_reports_by_report_id_get(report_id, query=None) -> dict:
    """GET /api/workbench/analytics/reports/{report_id} — 只读获取 Cloud DB 中固定ID对应的不可变治理报告"""
    return call_service(f"/api/workbench/analytics/reports/{report_id}", method="GET", query=query)


def workbench_backfills_list(query=None) -> dict:
    """GET /api/workbench/backfills — 运营查看回填任务状态、进度、checkpoint、请求ID和分Program结果"""
    return call_service("/api/workbench/backfills", method="GET", query=query)


def workbench_backfills_create(body=None, query=None) -> dict:
    """POST /api/workbench/backfills — 运营显式创建 enrichment 定向回填任务；dry-run 仅预览，禁止全量 membership、建 case 或通知"""
    result = call_service("/api/workbench/backfills", method="POST", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_backfills_by_id_get(id, query=None) -> dict:
    """GET /api/workbench/backfills/{id} — 运营查看单个回填任务详情"""
    return call_service(f"/api/workbench/backfills/{id}", method="GET", query=query)


def workbench_backfills_by_id_retry_create(id, body=None, query=None) -> dict:
    """POST /api/workbench/backfills/{id}/retry — 运营显式从 checkpoint 重试失败或中断的回填任务"""
    result = call_service(f"/api/workbench/backfills/{id}/retry", method="POST", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_batches_list(query=None) -> dict:
    """GET /api/workbench/batches — 只读返回真实持久化周度批次；无历史时返回空列表"""
    return call_service("/api/workbench/batches", method="GET", query=query)


def workbench_cases_list(query=None) -> dict:
    """GET /api/workbench/cases — 所有已登录使用者共享业务事件；收件箱可默认限定最新一致指标窗口，完整集合过滤后服务端分页"""
    return call_service("/api/workbench/cases", method="GET", query=query)


def workbench_cases_create(body=None, query=None) -> dict:
    """POST /api/workbench/cases — 从当前用户真实命中扫描幂等建立事件，不自动发送"""
    result = call_service("/api/workbench/cases", method="POST", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_cases_by_id_get(id, query=None) -> dict:
    """GET /api/workbench/cases/{id} — 共享事件的初始快照、结构化处置、审计、复查和通知；权限由当前鉴权身份与已验证人员映射服务端计算"""
    return call_service(f"/api/workbench/cases/{id}", method="GET", query=query)


def workbench_cases_by_id_commands_create(id, body=None, query=None) -> dict:
    """POST /api/workbench/cases/{id}/commands — 带版本和幂等键的统一分派、处置、复核状态机"""
    result = call_service(f"/api/workbench/cases/{id}/commands", method="POST", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_cases_by_id_notification_preview_create(id, body=None, query=None) -> dict:
    """POST /api/workbench/cases/{id}/notification-preview — 刷新权威人员映射并解析 Bot 域目标的无发送预览"""
    result = call_service(f"/api/workbench/cases/{id}/notification-preview", method="POST", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_cases_by_id_notify_create(id, body=None, query=None) -> dict:
    """POST /api/workbench/cases/{id}/notify — 显式向白名单测试人员发送卡片；要求确认 token 并保持 test 模式"""
    result = call_service(f"/api/workbench/cases/{id}/notify", method="POST", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_cases_by_id_rechecks_create(id, body=None, query=None) -> dict:
    """POST /api/workbench/cases/{id}/rechecks — 以当前AIME身份查询独立窗口真实CCR/NFS并保存复查"""
    result = call_service(f"/api/workbench/cases/{id}/rechecks", method="POST", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_casework_config_list(query=None) -> dict:
    """GET /api/workbench/casework/config — 处置模板、当前角色、测试接收目标和飞书配置状态"""
    return call_service("/api/workbench/casework/config", method="GET", query=query)


def workbench_comparisons_refresh_create(body=None, query=None) -> dict:
    """POST /api/workbench/comparisons/refresh — 按 account_id 与 program 定向刷新当前持久化行的比较窗口，不触发全量扫描、处置或通知"""
    result = call_service("/api/workbench/comparisons/refresh", method="POST", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_history_list(query=None) -> dict:
    """GET /api/workbench/history — 所有已登录使用者共享的最近十次扫描与处理记录"""
    return call_service("/api/workbench/history", method="GET", query=query)


def workbench_identity_mappings_list(query=None) -> dict:
    """GET /api/workbench/identity-mappings — 刷新并列出权威人员映射（敏感字段脱敏）"""
    return call_service("/api/workbench/identity-mappings", method="GET", query=query)


def workbench_identity_mappings_by_record_id_enabled_update(record_id, body=None, query=None) -> dict:
    """PUT /api/workbench/identity-mappings/{record_id}/enabled — 运营启用或停用人员映射；人工停用不会被后续 Sheet 同步覆盖"""
    result = call_service(f"/api/workbench/identity-mappings/{record_id}/enabled", method="PUT", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_notifications_batch_create(body=None, query=None) -> dict:
    """POST /api/workbench/notifications/batch — 使用统一通知服务批量预览或排队；默认 dry_run，正式执行要求每条独立有效 preview_token"""
    result = call_service("/api/workbench/notifications/batch", method="POST", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_read_model_list(query=None) -> dict:
    """GET /api/workbench/read-model — 四个主 Tab 共用的只读批次、筛选、卡片、事件与榜单契约"""
    return call_service("/api/workbench/read-model", method="GET", query=query)


def workbench_reported_reasons_refresh_create(body=None, query=None) -> dict:
    """POST /api/workbench/reported-reasons/refresh — 按 ET Account 与 Advertiser 定向刷新 Current Window 原因 Top3，仅更新关联持久化行"""
    result = call_service("/api/workbench/reported-reasons/refresh", method="POST", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_risk_policy_list(query=None) -> dict:
    """GET /api/workbench/risk-policy — 获取后端权威生效阈值、版本、权限与最近自动重判状态"""
    return call_service("/api/workbench/risk-policy", method="GET", query=query)


def workbench_risk_policy_update(body=None, query=None) -> dict:
    """PUT /api/workbench/risk-policy — 运营使用预览票据、CAS 与幂等键确认并提交新阈值配置，自动创建当前周重判任务"""
    result = call_service("/api/workbench/risk-policy", method="PUT", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_risk_policy_preview_create(body=None, query=None) -> dict:
    """POST /api/workbench/risk-policy/preview — 运营基于当前周持久化 ET/ST/THT 指标只读预览阈值草稿影响，不查询 Aeolus 或产生写副作用"""
    result = call_service("/api/workbench/risk-policy/preview", method="POST", body=body, query=query)
    notify_refresh("workbench")
    return result


def workbench_risk_policy_rejudgements_list(query=None) -> dict:
    """GET /api/workbench/risk-policy/rejudgements — 获取阈值配置自动重判任务状态与历史，供前端轮询"""
    return call_service("/api/workbench/risk-policy/rejudgements", method="GET", query=query)


def workbench_risk_policy_versions_list(query=None) -> dict:
    """GET /api/workbench/risk-policy/versions — 获取阈值配置版本与变更审计列表"""
    return call_service("/api/workbench/risk-policy/versions", method="GET", query=query)

