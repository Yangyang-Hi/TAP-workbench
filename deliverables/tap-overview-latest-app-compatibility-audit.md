# 最新 TAP 工作台与数据总览：只读兼容性审计

审计对象：用户上传 app_e5d1388d65ef1b49 (8).zip；SHA256 `721b28bdd0a0450923e9f049154ce2fe06bb80e8ed1b9a2417a7ddf5b2cb7590`。数据中心对比对象：源码交接包 v1 / 合并版 v8。

## 结论

可以增量接入，但应先更新数据中心的读取适配，不能把旧完整包覆盖到最新工作台。仅迁入 UI、完全不补后端查询能力，无法得到全部真实图表。没有发现为实现新总览而必须修改 Cloud DB 配置、通知投递或打标写入链路的需求；这不是实际环境零回归保证。

本次只读审查源码与差异，没有修改上传源码、安装运行服务、调用风神/Cloud/飞书、执行扫描、建单或处理业务事件。没有做最新版本合并构建及真实数据对拍。

## 已确认的兼容基础

- 与旧上传基线相比，最新包23个现有源码/IDL文件已变化；另有新的 gap-repair 源码，不能被旧版本替换。
- 数据中心23个候选文件与最新源码路径没有同名文件冲突。这只说明命名，不代表语义与构建已验证。
- 最新IDL包含48条路由，未包含四条 `/api/overview/*` 接口；需要追加定义并重生成，保留全部现有合同。另有手工Register路由，因此48不是全部运行时API数量。
- 本次上传的共享 aeolus_titan_probe.go、store_cloud.go、main.go、auth.ts 和工作台 index.tsx 与旧基线逐字节相同。旧 Overview 专用探针增量仍具备移植基础，但必须审查作用域、构建和非Overview回归。
- React19、Arco、lucide 等基本栈一致，真实宿主SDK仍为@aime-plugin/browser-sdk，沿用当前Provider/SDK构建即可，不必用独立前端包替换整个应用。

## 必须更新/明确的接口适配

| 模块 | 最新代码事实 | 合并建议 |
|---|---|---|
| Account/Revenue/P0等客观指标 | 尚无`/api/overview/*`查询合同；原governance通用接口不能提供这些真实聚合 | 追加认证GET及专属取数适配，沿用现有风神鉴权/VQS/固定过滤；不能只接UI |
| 风险客户、风险分布、占比 | 最新`wbRiskList`结合当前policy、绝对值和分组正增幅TopN；旧Overview按持久化row.Level及wbMatched计数 | 更新总览侧统计，复用当前权威风险选择/完整性语义，不另写阈值，不只根据critical/watch字段假定与风险页一致；保留已保存事实、当前规则版本和分母范围说明 |
| 周度ST批次 | 最新`wbPersistedBatches`从同一job拆分ST（`:ST`），配合STDone/STMembers标记完整度 | 调用最新批次聚合器，不能退回直接读原始state；核对ST合成ID与历史事件ScanID的关联，不能机械视为丢失事件 |
| 处置/通知汇总 | 最新read-model和analytics仍有直接SQLite读取路径；详情等使用Cloud Repository | 总览以现有Cloud Repository最新Case/成功Notice为准，复用权限；与风险列表不一致时明确报告，不顺带重构原列表或强制同步写入 |
| Quota | 现有`submissionQuotaData`、`loadQuotaSources`、`aggregateQuota`和ST快照可复用；旧Overview又单独组合ET/ST | 优先薄适配现有季度数据能力，保留Account/Brand单位、区域分母和缺失状态；无须同步Sheet或改提报流程 |
| 页面入口 | 已有四个Tab；data页内含Submission/Quota和客户指标 | 保留四页和既有data子页，新增受开关控制的数据总览入口，不直接替换旧data页、根路由或独立处理页 |

### 三个容易被“只读”名称掩盖的限制

1. `handler_governance.go` 的 identity-diagnostics、registry、sync-status、tabs 返回固定/占位内容，例如tabs为unavailable、cards为空，identity固定principal。这些接口存在不等于真实取数能力已完成，不应拿其200响应作为出数验收。
2. `/api/workbench/read-model?time_mode=custom` 实际会走`wbCustomQueryProgram`并发实时查询多个Program；不是保存批次的简单筛选。总览默认加载不能复用它触发大范围风神查询。weekly按单batch返回分页rows，最多500；不能只汇总第一页，更不能累加跨周重复客户。
3. `risk_level` 展示有`extreme`，持久化兼容路径仍可能是`critical`；旧总览分类不能仅加一个别名就视为完成适配。还要核对TopN正增幅规则、最新policy、Program×Tier×Region分组和客户/事件去重。风险占比只能称保存样本风险占比，不能称全量TAP风险率。

## Cloud与原链路保护

最新casework_cloud.go已补充从受保护列恢复BotFingerprint/TargetEmail/ResolvedOpenID；通知、身份映射、casework_store等也有变动。这些与投递前复核直接相关，必须保留，旧源码交接包不包含并不要求替换这些实现。

不修改DB_APP_ID/DB_API_KEY/DB_BASE_URL、共享范围、数据库表、Case ID、状态机、CAS、Preview Token、收件人解析、Outbox和操作审计。总览不提供发送/打标按钮，不新增通知相关调用。读取失败不当作零，不通过补扫描/建事件填数据。草稿是否与生产共享库需实际确认，代码/页面开关不等于数据隔离。

## 给AIME的更新任务（附旧交接包一起使用）

请先以当前成功工作台为底版，根据本审计更新“数据总览侧适配”，再增量合并。旧交接包v1仅作为源码素材，不能直接覆盖。

1. 保留现有四页，在当前原生布局中以feature flag新增“数据总览”，关闭开关时原四页和处理深链照常可用。flag也应阻止新模块挂载/请求，不只是隐藏导航。沿用当前Provider、AuthGuard、typed client、样式和构建。
2. 追加四条认证GET或经审查的等价接口，重生成typed client；保持当前全部旧路由、请求/响应和权限不变。追加Overview专属风神分支，回归原ET/ST/THT查询；避免复制第二套通用数据源合同。
3. 更新风险/处置适配：读取最新批次（包括ST拆分）、完整范围、当前权威风险集合与Cloud事件通知，核对TopN、extreme/critical、客户键、Alert ID、窗口及当前状态。不能从单页rows或旧row.Level独立推断全部风险。
4. 复用现有Quota读取聚合（审查调用链，只读无业务写入），跨季度分开显示；原Submitter/Advertiser分母限制保留，客观分布不套Program筛选。
5. 不把占位governance接口、custom实时查询或分页read-model误用为完整已保存总览。多周范围由后端只读聚合，不在浏览器拼不完整分页造成假数。
6. 保留AIME现场最新的网关、MIME、代理前缀、启动产物修复。此次上传无法证明另一草稿App的全部现场修复也已包含，必须在目标环境核对，禁止用旧构建/静态路由补丁覆盖。
7. 验证总览按时间/Region出数并与源端对拍；原飞书卡片入口、事件详情、打标权限和操作历史先只读回归。真实发消息/提交打标/正式发布须另行明确对象和影响，不为了验收直接写已有生产事件。
8. 先交草稿与代码差异、验证证据及缺口，后发布。对业务链路无法保持不变的冲突先报告具体位置，不能静默覆盖。

## 验收边界

本审计确认的是代码层面需要哪些适配，不代表新合并包已完成，也不能保证生产链路绝对无回归。Account曾由用户验证成功；其他报表权限、字段、单位、完整性和真实数值仍须AIME现场逐项确认。关闭新页面可停止其新请求，但不能撤销已经发生的数据库业务操作，故本阶段不做业务写入。
