# Rigarus — 中文使用说明书

[English user guide](USER-GUIDE.en.md) · [中文项目概览](README.zh-CN.md)

**文档版本：**2026-11-26 工程预览。**源码基线：**main `8f6e547`（已合并122），加等待审核的 Issue18 只读影响预览。
软件界面为英文，本文保留实际英文按钮名称，方便对照。使用前核对所安装构建的提交；
本说明书不是客户验收签收或生产派工许可。

## 目录

- [1. 适用范围与功能状态](#scope)
- [2. 安装与启动](#startup)
- [3. 导航与搜索](#navigation)
- [4. 项目与工作项](#projects)
- [5. Crew、员工、Foreman 与 Rig](#resources)
- [6. 旧半天 Draft 生命周期](#drafts)
- [7. 明确选择实际人员](#staffing)
- [8. Crew 与 Project 工作日历](#calendars)
- [9. 员工可用性](#availability)
- [10. Employee Week 员工周历](#employee-week)
- [11. Review 与 Locate 定位](#locate)
- [12. 导入预览与批量新增](#imports)
- [13. 整天推荐与状态解释](#recommendations)
- [14. 本地数据、升级与恢复](#data)
- [15. 常见问题](#troubleshooting)
- [16. 合成数据练习清单](#practice)

<a id="scope"></a>
## 1. 适用范围与功能状态

Rigarus 面向一名本地调度员，运行于 Windows，无需软件账号或云日历，
优先支持 Windows11 x64。

所有者已确认：新排班最小单位为 **Full Day（整天）**。目前桌面仍显示
**旧 AM/PM 半天兼容控件**。下述半天步骤仅用于查看既有记录，或在维护人员提供的
隔离合成资料中练习，不能当作新的整天正式派工流程。不要擅自将两条旧记录合并，
将半天估算进位，或认为 AM/PM 证据能够证明全天合格。

| 功能 | 本基线状态 |
| --- | --- |
| 项目、Crew、员工、Foreman、Rig 台账 | 桌面可管理 |
| 周排班板、既有草稿、明确选人、Locate | 桌面旧数据兼容流程可用 |
| 工作日历、员工可用性 | 桌面为半天控件；另有独立每日后端 |
| 整天 Draft、每日日期生成及资源检查 | 后端工程能力；生产每日写入仍关闭 |
| 整天 WorkItem Auto-Recommend | 只读日期候选、解释及 Current/Stale 检查 |
| 整天周排班板 | 只读新旧记录工作台、类型化 Locate 及已保存资源检查 |
| 独立每日编辑 | 隔离合成测试配置内新增／编辑／取消、明确选人及请求恢复；生产 Save 仍禁用 |
| 人工 Apply、锁定、事务复核、可恢复版本 | 等待完整操作流程 |
| 正式排班及公司/Crew/员工 PDF、Excel | 尚不可用，导出按钮仍禁用 |

所有 Draft 和候选保持 **Validation Pending（待验证）**，不能当作已确认员工日程
对外分发。某一项资源检查通过，不等于整项派工已批准。

### 独立整天编辑器（工程预览）

从 **New / Recover Full Day Draft** 或整天卡片的 **Edit Full Day Draft** 进入。
普通安装仅预览，Save 禁用；维护人员的合成测试写入配置不等于客户投产许可。
选择已保存 WorkItem、Crew、完整本地日期和备注，明确选择“人员未记录”或实际员工名单。
Home Crew 不会自动成为出勤；更改工作项、Crew 或日期后须重新确认人员名单。
**Close without saving** 不修改 Draft。取消已保存记录须确认类型、ID 和修订号，
保留原备注与人员历史，仅从活动周表移除该整天记录，不删除旧半天记录。
重开后可通过 **Open saved Full Day ID, including cancelled** 查询取消记录，
使用 **Read latest 100 immutable Draft revisions** 查看最近100次不可覆盖修订。

Stale revision 会保留未提交输入；明确加载当前保存值会替换输入供重新核对，不会强盖新版本。
结果 Unknown 时保留原恢复请求，先用 **Resolve original request** 查询回执；
未查到不代表未保存。必要时只能 **Retry same unchanged request**，不能另建请求盲目重试。
明确已保存但周表刷新失败时，点击 **Retry weekly refresh — no writes**，不要再次 Save。
本地恢复日志读取失败时保留证据，不得静默清空。逐项查看 Blocked／Pending；
编辑器不开放推荐 Apply 或正式 Publish。

默认 **Job Schedule / Crew Board** 是只读 Full Day 工作台，两张表使用同一周快照。
蓝色整天卡保留无 Slot 的日期，黄色 Legacy AM/PM 保留原 ID/时段并标记 Needs Review。
打开卡片查看实际人员、原备注、记录的 Rig ID 和独立资源检查；Home roster 只是参考。
筛选不会从 **Review saved checks** 中移除记录。检查仅代表加载时观察，资料变化后点击
**Reload week**。

展开 **Locate & Auto-Recommend**，选择 **FullDayDraft** 或 **LegacyHalfDay** 和
准确的 Saved ID；整数相同也属于不同记录。Locate 重新读取当前状态，显示对应周、
处理不兼容筛选并聚焦准确卡片。记录删除、取消或读取失败时不会跳到另一类型。
详情和检查列表使用相同类型化 Locate；按 Enter 可以打开已聚焦卡片。
选择 WorkItem 或详情的 **Auto-Recommend** 可打开原有只读 Remaining Days 推荐。
推荐和 Locate 都不会保存排班。

独立每日编辑器尚未提供。**Legacy compatibility** 单独保留旧半天流程，使用
**Open Full Day workbench** 返回。全局 Schedule 搜索目前仅索引旧访问，整天 ID
使用类型化 Locator；Employee Week 和日历录入仍为旧兼容控件。

<a id="startup"></a>
## 2. 安装与启动

1. 向维护人员获取审核过、可对应到具体提交的 Windows x64 工程安装包。
   核对文件名、SHA-256，以及随包提供的 `build.json`（如有）。
   CI 产物不会自动成为客户发行版。
2. 按获准流程安装。安装包包含本地 Python 服务与运行时，以及需要时使用的离线
   WebView2 安装程序。操作电脑无需安装 Python、Node.js、Rust 或 .NET SDK。
3. 在 Windows 开始菜单启动 **Rigarus Dispatch**。正常运行使用本地数据、无需登录；
   默认进入 **Schedule → Job Schedule**。
4. 使用相同 Windows 账号返回默认资料。练习时请维护人员准备隔离合成资料，
   不要在客户数据中试操作。

必须保留完整安装内容；仅复制桌面 EXE 会缺少配套服务和资源。
源码构建见[README](../README.md#develop-and-test-windows)，一般操作人员无需执行开发命令。

<a id="navigation"></a>
## 3. 导航与搜索

| 位置 | 用途 |
| --- | --- |
| Schedule | Job Schedule、Crew Board、Employee Week、Working calendars，以及已有概览/设备视图 |
| Project Management | 项目、工作项及 Bulk Add Projects |
| People | Employees、Crews、Availability |
| Items | Rig 台账 |
| Reports | Weekly Export 及尚缺条件 |
| Data | Import preview 与独立的合成 Demo note |
| Settings / Help | 本机外观设置、当前页面帮助 |

通过上一周/下一周、**Today**，或日期输入框加 **Go** 切换本地周日到周六。
日期使用 `YYYY-MM-DD`。Crew/Project 筛选只改变显示，不修改已保存安排。
较长的排班板需在内部滚动以查看后面的行；跨日条带仍包含独立的已保存访问记录。

使用顶部搜索或 **Ctrl+K**，选择记录类型后打开结果。Schedule 结果可定位到已保存卡片。
使用 **Tab / Shift+Tab** 移动焦点，**Enter/Space** 操作聚焦控件；等待加载并遵守禁用状态。
**Settings → Appearance** 的修改会立即预览；**Save appearance** 才保存到本机，
取消会恢复此前设置。

<a id="projects"></a>
## 4. 项目与工作项

1. 打开 **Project Management → New project**。
2. 填写 **Job #、Site ID** 和站点名称。编号按文本保留前导零；
   练习可使用 `SYN-1001` 等虚构编号。
3. 需要时点击 **Add work item**，选择 Type，填写合法的
   **Required crews** 与 **Estimated half-days**。这是现有旧表单；
   Estimated half-days 是历史估算元数据，不是已确认的 Remaining Days。
4. 点击 **Save project**，通过 Search 找回并打开记录。修改既有项目时使用编辑，
   不要重复新建。

按字段错误提示修正后重试。项目必须有 WorkItem 才能安排访问。
同一 Project 的 Civil/Tower 可以是独立工作项，但都继承父项目工作日历。
保存项目不会自动排班或减少剩余工期，也不能从 Draft 推断已经完成的工作量。

<a id="resources"></a>
## 5. Crew、员工、Foreman 与 Rig

- **People → Crews → New crew：**填写名称和类型并保存。通过 **Edit** 修改；
  通过 **Foreman** 查看、设置或清除当前负责人，检查历史后使用 **Save Foreman**。
- **People → Employees → New employee：**选择 Home Crew，填写界面中的姓名、
  Level、资格标记和 Active 状态，点击 **Save employee**。选择 Home Crew 前应先创建 Crew。
- **Items → New rig：**记录车辆编号、类型、可选默认 Crew 和备注，点击 **Save rig**。

Home Crew 是日常归属，不代表每天在每个任务中出勤。设置 Foreman 或借调不会修改
Home Crew；Level 也不等于专业证书。Rig 的 Active 或默认 Crew 关联，不能证明当天
实际用车、检查合格或司机认可。每日资源证据编辑尚未接入这些界面。

<a id="drafts"></a>
## 6. 旧半天 Draft 生命周期

先点击 **Legacy compatibility**；下列旧编辑器不是新每日周表的保存入口。

**仅限兼容检查与合成练习：**当前编辑器使用 AM/PM，本基线没有生产整天编辑器。

1. 打开 **Schedule → Job Schedule**，选择周次并点击 **Assign Work Item**。
2. 选择 Project、WorkItem、Crew，输入本地日期及界面中的旧半天时段，按需填写备注。
3. 检查日历提示，点击 **Save to Draft** 并等待结果。保存前点击 **Cancel** 不写入。
4. 点击已保存卡片，查看稳定 **Draft #**、日期、Crew、人员、备注和 Revision。
   使用 **Edit draft → Save to Draft** 修改。
5. 取消已保存访问时选择 **Cancel draft → Confirm cancellation**；
   **Keep draft** 则保留。取消会保留身份和历史、释放占用，不会取消同工作项的其他有效访问。
6. 在合成练习中关闭并重启程序，检查保存是否持久存在。

已有 Crew/时段冲突会被拒绝。每日存储也保护整天与旧有效半天之间的占用重叠，
不能通过改成另一 Slot 绕过。保存结果不确定时，先重新加载，不能连续盲目重试。
更改 WorkItem/Crew/日期/时段后须重新确认人员；旧记录仅改备注会保留人员选择。

<a id="staffing"></a>
## 7. 明确选择实际人员

1. 打开已保存的 Draft 卡片，找到 **Draft workers**。
2. 点击 **Choose workers**，使用 **Find employee** 查找并明确勾选这次访问的人员。
3. 查看员工记录的可用性、Home Crew 及借调信息。
4. 点击 **Save workers to Draft**；放弃修改使用 **Cancel worker changes**。
   独立的可用性读取失败时，可使用 **Reload worker availability**。

Employee Week 只使用已保存的明确选择，不会自动把整个 Home Crew 安排进去。
空名单或缺失名单都不代表安全人数；Available 不是派工许可，Unavailable 也不会自动
移除已选择的 Draft 员工。借调还必须复核原 Crew 的人数、司机与资质，
桌面勾选本身没有完成全部检查。

<a id="calendars"></a>
## 8. Crew 与 Project 工作日历

1. 打开 **Schedule → Working calendars**。
2. 选择 **Crew** 或 **Project**，选择记录及周次。
3. 点击日历格，或 **Record working dates**。填写包含首尾的日期范围、当前界面的
   旧覆盖范围，以及 **Can work / Cannot work / Not recorded**。
4. 使用 **Save working dates** 明确替换所选范围，或取消。
   **Calendar change history** 查看历史；过期或结果不确定时使用 **Reload calendar**。

WorkItem 继承父 Project，没有单独覆盖日历。两套日历都明确允许工作才是日历匹配。
空白表示未知，不代表默认周一至周五、节假日或周末开放。
**Calendar matched** 只是一项日历结果，不提供人员、司机、Rig 或周末批准。
当前旧控件的 **Full day** 表示写入两个半天，不等于新的独立每日合同或自动历史转换。

<a id="availability"></a>
## 9. 员工可用性

1. 打开 **People → Availability**，选择员工与周次。
2. 点击日历格或 **Record availability**。
3. 选择包含首尾的日期范围、界面覆盖范围，以及
   **Available / Unavailable / Not recorded**，点击 **Save availability**。
4. 放弃当前修改使用 **Cancel availability changes**。可查看界面历史；
   过期或读取失败后先重新加载。

这些桌面控件仍使用旧 Full day/AM/PM 表单。仅半天 Available 不能证明全天 Available，
Not recorded 保持未知。可用性与实际人员、请假批准、认可司机、资质和周末同意相互独立；
更改可用性不会重写排班。

<a id="employee-week"></a>
## 10. Employee Week 员工周历

打开 **Schedule → Employee Week**，选择员工和周次。界面只显示有明确已保存人员关联的
访问，同时展示借调 Crew 和独立记录的可用性；Home Crew 不会自动生成访问记录。
点击访问查看只读详情，读取失败后使用 **Reload employee week**。

**Export preview** 是界面内的规划快照，标注 **DRAFT – NOT CONFIRMED**。
其中 **Export PDF / Export Excel** 仍禁用，不会生成可发送的正式日程或联系员工。

<a id="locate"></a>
## 11. Review 与 Locate 定位

1. 在 Schedule 打开 **Review & Publish**。列表包含当周已保存访问，
   即使它们被排班板筛选隐藏。
2. 点击相应记录的 **Locate**。也可在 Draft 详情使用
   **Locate in Job Schedule**，或打开全局搜索中的 Schedule 结果。
3. 来源弹窗关闭，切到记录所在本地周的 **Job Schedule / 1 Week**，
   显示准确卡片并移动键盘焦点。兼容筛选保留，挡住目标的筛选或行上限可能调整。
4. 高亮约两秒后清除。减少动态效果时使用静态强调，连续定位替换上一次提示。
   焦点停在卡片时可按 Enter 打开详情。

Locate 按稳定排班身份定位，因此同一天 AM 与 PM 可区分，操作不修改 SQLite。
已取消或找不到的目标会显示反馈，不会自动重建；数据过期先重新加载再试。
当前 Review 显示日历和人员记录反馈，不等于完整的每日资源验证。
**Publish schedule unavailable** 仍禁用。

<a id="imports"></a>
## 12. 导入预览与批量新增

以下是不同入口，写入行为不同：

| 入口 | 输入与效果 |
| --- | --- |
| Data → Import preview | 本地不超过5MiB的 `.xlsx`；**Preview workbook** 只读，**Cancel preview** 清除预览 |
| Project Management → Bulk Add Projects | 粘贴 CSV/Excel TAB 文本或本地 `.xlsx`；**Preview projects** 后显式 **Confirm … projects** 可以新建项目 |

**Import preview** 第一行使用 **Job #、Site ID、Site Name**；
可选字段以该页面说明为准。检查诊断及来源单元格，这不是完整历史工作簿导入器。

**Bulk Add Projects** 使用下列三个表头，一行一个项目，编号保留文本：

```csv
Project Number,Site ID,Site Name
SYN-1001,0010,Synthetic North Site
SYN-1002,0020,Synthetic South Site
```

确认前检查 Ready/Skipped 数量及错误。已有或重复项目跳过，不覆盖。
更改文本、文件或选项卡后必须重新预览；确认前取消不写入。
Bulk Add 不会创建每日排班、推断工作项或自动核对历史实际施工。

<a id="recommendations"></a>
## 13. 整天推荐与状态解释

在 **Project Management** 打开已保存 Project，选择其 WorkItem 旁的
**Auto-Recommend**。它只读取每日快照，不保存排班。

1. 输入正整数 **Remaining Days**，并明确勾选本次确认；不会预填半天估算或扣减旧访问。
2. 选择候选 Crew；这些是替代方案，不是同时出勤人员。选择含首尾的本地日期范围
   （最多366天）及1–10个候选（默认3）。
3. 点击 **Preview full-day dates**；默认 **Earliest Finish**，切换
   **Earliest Start** 会按相同输入重新生成并排序。
4. 展开 **Dates and missing checks**，查看累计/跳过日期、原因及缺失检查次数。
   不足容量会显示 Needs Review，不伪造完工日期；数量上限只隐藏额外完整日期候选。
5. **Recheck inputs** 区分 Current、Stale、Unavailable；回到窗口也会重新检查。
   Current 仅代表上次读取时相同，不预留资源。Stale 必须重建；修改输入会清空旧结果。
6. **Close preview** 或 Escape 关闭并返回入口焦点；重开时工期为空且尚未确认。

所有卡片保持 **Validation pending**，不选择实际人员或 Rig，**Apply to Draft**
及 **Publish** 禁用。生产每日写入、每日日历及同意证据编辑仍关闭或尚未实现。
旧 AM/PM 日历不会生成整天事实；没有明确每日资料时应得到 Unknown/Needs Review。
工程演示请维护人员提供隔离合成资料，不要手工修改客户数据库。

周末必须由所有相关员工 Confirmed；部分确认、Pending 或拒绝不能用该周末缩短工期。

| 状态 | 含义与处理 |
| --- | --- |
| Draft / Validation Pending | 已保存规划，不能当作正式安排 |
| Calendar matched | Crew 与 Project 日历匹配，其他检查仍独立 |
| Pending / Not recorded / Unknown | 证据缺失或未解决，不能默认可用或已批准 |
| Blocked / Declined | 已知阻断或拒绝，处理后重新生成/审核 |
| Needs Review / Legacy / Conversion Required | 信息不足或不兼容，保留原始记录并明确审核 |
| Current | 本次检查时观察输入相同，不是未来写入锁 |
| Stale | 输入发生变化，重建候选，不能继续使用旧日期/证据 |

所有候选保持 **Apply=false / Publish=false**。Reports 尚不能导出经验证的
公司/Crew/员工日程。Before/After、锁定、事务内人工 Apply、审计和可恢复版本完善后，
才可继续正式派工与导出流程。

<a id="impact-preview"></a>
### Preview Impact（只读工程切片）

从 WorkItem 的 Auto-Recommend 弹窗输入正整数 Remaining Days，明确勾选确认，
选择候选 Crew、本地开始日期及规划终点，再点击 **Preview Impact**。
加载后会列出本范围内既有记录。明确勾选要在内存中替换的 FullDayDraft ID
和修订，再点 **Recompute impact**；未勾选时，所有既有占用仍被保留。
旧半天记录显示为 Legacy / Needs Review，不能勾选为自动转换对象。

对照 **Before · Saved** 与 **After · Proposed** 的日期、既有实际人员和车辆、
拟议资源缺口、跳过日期及资源原因。Before 的 Remaining Days 显示 **Not recorded**，
不能用已保存五个日期推断还需五天。其他任务不自动移动；锁和连锁依赖缺少可靠支持时
显示 **Needs Review / Unsupported**，不能理解为没有影响。

用 **Recheck inputs** 核对 Current / Stale。Stale 必须重新计算；读取错误不代表安全。
选中记录的修订变化后，使用 **Reload saved visits — clear selection** 清空旧选择并
重新读取，核对新 revision 后再次明确勾选；不会将旧意图静默绑定到新修订。
**Cancel / close preview** 或 Escape 关闭时不修改 SQLite，焦点回到入口按钮。
Apply、Publish 和生产每日写入继续关闭；此功能不能用于正式派工。
参见[合成示例](../samples/synthetic-only/impact-preview.md)。

<a id="data"></a>
## 14. 本地数据、升级与恢复

默认数据库：`%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db`。
使用同一个 Windows 账号/资料。客户信息、附件、WAL、备份和诊断资料仅保存在授权本地环境。

目前没有完整的操作员 Backup/Restore 界面。升级或恢复前请维护人员建立并验证一致备份。
不能只复制运行中的 `rigarus.db`，不能删除 `-wal/-shm`、手改 SQL 或删除迁移历史。
维护性复制前，先关闭所有 Rigarus 窗口，再由维护人员确认本地服务已停止；
保留完整相关资料并验证副本后，才能调整原始文件。

当前启动包含增量迁移和已验证的升级前备份保护。旧构建可能拒绝新版数据库。
恢复需要独立、已验证的备份及兼容程序，同时保留新版资料以核对后续新增修改；
不要覆盖正在使用的数据库强行降级。详见[数据保护说明](07-SECURITY-BACKUP.md)。

<a id="troubleshooting"></a>
## 15. 常见问题

| 现象 | 处理 |
| --- | --- |
| 排班板为空 | 检查周次、Crew/Project 筛选及是否有已保存访问；没有可见卡片不等于项目完成 |
| 没有 WorkItem 或员工 | 先补充对应主数据再重新加载；Home Crew 不会自动填充人员 |
| Calendar pending/conflict | 核对 Crew 和父 Project 两套日期；未知与读取失败是不同情况 |
| Revision changed / Stale | 重新加载当前记录，核对变化后再明确编辑 |
| 保存结果不确定 | 先加载确认是否已写入，再决定是否重试 |
| 已保存但刷新失败 | 写入可能已经成功；先重新加载，避免重复新增 |
| 本地服务不可用 | 关闭并重开程序；持续失败请维护人员核对完整安装内容 |
| 数据库锁定或不可用 | 关闭其他 Rigarus 实例，检查本地目录权限；不能删除数据库/WAL |
| 需要兼容版本 | 停止操作，使用匹配程序或独立验证过的恢复副本 |
| Apply/Publish/导出禁用 | 本基线的预期状态，没有获准绕过方式 |

请求支持时记录构建提交/版本、操作步骤、可见错误及预期结果。
仅分享脱敏描述和合成复现；原始客户工作簿、数据库、含真实员工的截图及日志保持本地。

<a id="practice"></a>
## 16. 合成数据练习清单

使用维护人员提供的隔离合成资料：

1. 新建 `SYN-1001`、Civil WorkItem、Crew 及两名虚构员工。
2. 查看/记录旧 Crew/Project 日历与员工可用性。
3. 保存旧 Draft，明确选择人员，检查 Employee Week。
4. 从 Review、详情或搜索 Locate，确认准确日期、卡片与高亮。
5. 修改备注，重新加载/重开，再明确取消访问；检查其他访问不变、表单 Cancel 不写入。
6. 预览上面的合成 CSV，仅在准备好后确认 Bulk Add。
7. 确认 Publish/PDF/Excel 仍不可用，没有文件发送给员工。

本文对照源码中的标签与合同核对。本次文档修改**不代表新执行了原生 GUI、
离线安装或客户 UAT**。实际条件见[工程验收索引](05-DEMO-ACCEPTANCE.md)。
