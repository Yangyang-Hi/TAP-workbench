# TAP数据中心 v7 · 完整组件验证包

[下载完整安装ZIP](tap-data-center-v7-app_55cc4d81544026ab.zip)。若文件页未自动下载，点击右上角Download raw file。

安装目标仍是 **app_55cc4d81544026ab**。这是完整源码及可执行发布二进制包，不需改App ID、服务名或启动命令。原v6包继续保留。

本次补齐原生账户/营收总卡、Approval/Banned周趋势、Ads FDR/Overturned Account周趋势、区域×Tier账户/营收分布、TAP/Non-TAP区域对比。原有分布、CCR、Quota、治理与Submitter组件保留。支持起止日期、Region，Tier统一筛选继续暂缓。账户快照与区间营收分开；不能核实完整分母时不算占比；缺失/失败不补0。

本地验证：79项前端测试；31项总览Go顶层测试含race和子测试；17项已有取数合同/Quota/Reported reason回归；TypeScript、11项生成一致性、标准release构建、桌面/手机检查、实际ZIP解压启动及开发产物不可执行回退检查通过。18个数据接口无身份均401；扫描/建单/通知回调POST均404。没有运行原完整私有SDK前端/无关Go全套。

**组件代码已补齐，新增真实报表尚待AIME对拍。** 源字段、区域映射、权限或原生指标不符合合同的模块会显示具体不可用/诊断，而不是复制静态图或猜数。尤其FDR/Overturned的week/Tier ID从真实schema绑定，Audit Region目前只确认APAC/EUI/LATAM/METAP/NA；CNOB等未确认映射不会用Global或APAC代替。Revenue币种与率的缩放仍保留待确认源值。

安装后先用QTD/Global和APAC核对各RID，再测CNOB、历史日期及跨季度。若失败，点击页面“下载本次查询记录”导出JSON。完整模块/来源/时间语义/验收步骤位于包内docs/overview/迁移清单.md和取数与验收.md。截图标明为界面测试样例，非真实风神数据。

独立App不搬运主工作台的Cloud事件、扫描历史或ST季度名单；缺少时保持未接入。主工作台合并等待用户验收后执行，本轮没有合并或修改其风险预警/推送/处置。后续审查资料另存[tap-data-center-v7-integration.zip](tap-data-center-v7-integration.zip)，不是安装包。

ZIP SHA256：`b90e758616dc24d902a5334a0ed0334baa50b110cc536425964edb0c6605aeff`。
