# TAP UI优化 v2：以最新(9).zip及草稿为底版

本版替代UI v1，唯一基线为用户上传app_e5d1388d65ef1b49 (9).zip，SHA256：aa991ef6c762a73d2f4e002d092502f315a9df0563d86366814295a165c9894f。App仍为app_e5d1388d65ef1b49。

与上一份上传包逐文件比对，仅前端package.json的build命令不同。本版保留最新命令pnpm run typecheck && vite build，并以实际ZIP文件内容而非Git提交状态为准；没有将未提交草稿回退到仓库旧版本。

## 优化内容

- 深蓝黑主题、青色重点、清晰对比、统一卡片/表格/输入框/按钮/抽屉/独立处理页。
- 业务数据与预警记录筛选区域分别标注，控件重新排版，保留全部筛选及原触发方式。
- 现有按钮仅改善文案与呈现：“刷新预警记录”“导出预警CSV”，handler和参数不变。
- 首页模块标题与说明精简；保留P0区域对比、P1 Region×Tier、Approval季度等实际口径，不称周趋势。
- ST/HT/BT/ET环图配色统一为绿/蓝/橙/紫；值、占比、排序和绘图计算不变。
- Revenue长数字与进度条分行、表格数字回到适合阅读的尺寸、窄屏和键盘焦点优化。

## 本次严格不改

- 四个主Tab仍为治理总览、风险监控与预警、治理效果分析、运营数据中心；原tab键、入口、详情、历史及飞书深链不变。
- 无新增阅读辅助脚本，不改main.tsx、Provider、AuthGuard、SDK、鉴权、路由和构建配置。
- 后端、API定义、所有*.gen.*、typed client、config、skills、Cloud、扫描、通知、read-model、Case/Alert/scan/row ID、Top10、报告生成与HTML下载逻辑逐字节保留。
- shared-filters.tsx、casework.tsx、casework-task.tsx、casework-analytics.tsx、overview-feature.ts、业务API工具保留原样。没有变更默认QTD、日期窗口、Region/Tier/Program/周度/保护时间/Submitter/Quota筛选、任何query/body或触发时机。
- 不修复源数据缺口，不重算CCR、Account、Quota，不把null/失败改成0。不截断极端客户。
- 正式/测试通知文字和确认流程保持，不只靠颜色区分。

## 构建与验证

本地缺少私有@aime-plugin/browser-sdk，不用模拟SDK替换生产。保留用户上传的真实宿主和业务编译模块；主模块仅执行有清单的显示文字和配色替换，验证结果逐字节等于白名单变换。文件重命名为新内容哈希避免缓存旧资源；新增独立CSS通过原页面加载。原其他JS/CSS模块全部不变。

同样改动已写入源码。global.css导入纯展示CSS，其余修改限定在pages/governance两个展示组件和一处匹配文案的前端测试。AIME具备真实私有依赖时可按现有标准构建从源码重新生成；无需替换SDK或恢复旧构建脚本。

- 61项原有前端回归通过；只同步一处文案断言，未跳过/删除业务断言。宿主相关home测试未在本地验证，不把它算通过。
- CSS构建及编译主模块语法检查通过。
- 原生完整前端/TypeScript构建未在本地验证（缺私有SDK；workbench专用tsconfig另有?raw声明问题），不能把UI资源构建说成完整宿主重编。
- Chromium示例响应验证四页、旧任务深链与返回、390px窄屏、筛选与失败态，无pageerror、无整页横向溢出、零业务写请求。测试替身仅在包外QA目录，不进入生产应用；图片均有示例水印。
- 解压实际交付ZIP检查页面/JS/CSS响应及未登录API鉴权，不启动生产main/workers。
- 没有真实风神/Cloud/飞书取数或消息、打标验证；仍需AIME安装后的实际环境验收。

## 安装与合并

完整ZIP只用于原App app_e5d1388d65ef1b49，先保留原包，在草稿验收，不自动发布。新上传的业务配置和App元数据原样保留。

若AIME在此ZIP上传后又修改了代码，不覆盖完整包。使用v2源码增量补丁：先检查冲突，人工合入并使用真实SDK构建。补丁只含展示源码与样式，不含旧后端、旧API或旧包配置。

回退使用本次上传基线ZIP恢复UI文件。业务数据本次没有写入，代码回退不代替业务数据回滚。

包不含node_modules、.aime_build、日志、数据库、.env、旧导出业务报告或CDN缓存记录。docs/ui-refresh中仅为示例界面图及验证清单。

ZIP SHA256: 2871c9f07d03324c24c7e08eb5a9b446f53db117ea072bf4f800d703a94efdd9
