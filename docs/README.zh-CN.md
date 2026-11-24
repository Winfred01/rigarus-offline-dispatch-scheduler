# Rigarus 离线调度排班工具

[English](../README.md) · **简体中文**

Rigarus 是一款面向**单名办公室调度员**的 Windows 离线桌面排班软件，**无需注册或登录账号**即可使用。技术栈为 **Tauri/Rust + React/TypeScript + 随应用打包的 Python FastAPI + 本地 SQLite**。运行时不需要 Google Calendar、云同步或外部排班服务，软件界面为英文。

> **工程预览版 · 2026-11-24。** GitHub 代码已合并不代表客户正式验收。Demo A–F、完整派工安全检查、正式分发及 UAT 仍未完成。开发、演示和 CI 应使用合成数据；Draft 不等于正式施工派工。

## 当前已实现的功能

| 模块 | 当前工程预览能力 |
| --- | --- |
| **Schedule → Job Schedule / Crew Board** | 基于同一份已保存 Draft 的周日—周六排班表；按本地日期、暂定 AM/PM 半天时段新增、编辑、明确取消并重开排班。同一 Crew/时段的已知占用冲突会拒绝保存；连续安排可呈现跨日条带。支持本地搜索和切换周次。 |
| **Project Management** | 新增、编辑、搜索、排序 Projects 和 Small/Civil/Tower/Other WorkItems。Bulk Add 支持粘贴 CSV、Excel TAB 分隔文本或上传本地 `.xlsx`；先只读预览重复/错误，再由调度员明确确认事务式新增。 |
| **People → Employees / Crews** | 管理员工、Civil/Tower 班组、Home Crew、技能等级、Foreman 任命和历史；能够为具体 Draft 安排显式选择员工，临时加入其他 Crew **不会修改 Home Crew**。 |
| **People → Availability** | 按含首尾日期范围记录 Available、Unavailable、Not recorded，支持全天、AM、PM 及变更历史。这只是计划参考，不代表通过派工资格审核。 |
| **Schedule → Employee Week** | 只读显示某名员工**明确被分配**的周任务、借调班组和可用性。仅有 Home Crew 归属不能推定实际出勤；个人预览明确标记 **DRAFT – NOT CONFIRMED**。 |
| **Schedule → Working calendars** | 分别维护 Crew 与 Project 的 Working、NotWorking、Unknown AM/PM 日期；WorkItem 继承其父 Project 日历。冲突/未知在 Draft 中提示，不会默认周一至周五、周末或节假日可以工作。 |
| **Items / Data / 本机工具** | Rig 主数据及可选默认 Crew（不等于当天实际用车）；Excel 只读导入预览；独立演示备注；全局搜索（`Ctrl+K`）、外观设置和 Help。 |

### 自动排班：目前只完成内部计算核心

已经合并的 [#28 第一阶段 PR #91](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/pull/91) 和 [第二阶段 PR #92](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/pull/92) 是**纯 Python 算法模块**，**尚不是桌面软件里可直接点击的 Auto Schedule 功能**。现阶段支持：

- 对**单个 WorkItem、单支 Crew**，使用**操作员明确确认的剩余半天数**及提供的 Crew/父 Project 日历、占用快照生成日期。
- 跨不可工作间隔累计 AM/PM，说明跳过时段原因；若工期或可用容量不足，返回 **Needs Review**，不伪造完工日期。
- 根据**最早完工**（默认）或**最早开工**排序候选，排除已有明确硬阻断，缺少安全证据时继续 Pending。

算法**尚未接入可信的数据库排班快照、API 或桌面 UI**。人员双占用、司机/资质、最低人数、实际 Rig、周末同意等校验尚不完整。所有候选均为 **Validation pending；Apply = false；Publish = false**。详见[日期生成器工程验收记录](acceptance/2026-11-24-issue-28-generator.md)。

## 尚未具备的正式业务功能

- 完整人员/Rig 同时段占用、认可司机、技能资质、最低人数、Rig 维修换车和实际出勤人员的周末同意等安全门槛（[#15](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues/15)、[#23–#27](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues)）。
- 可信推荐数据适配、可安全 Apply 的多方案审查、延期/提前完工连锁调整、锁定及不可变 **Published** 排班版本（[#18–#29](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/issues)）。
- 公司、Crew 或员工的**正式 PDF/XLSX 派工导出**。`Reports → Weekly Export` 会列出尚未满足的检查，相关按钮未开放；Employee Week 的草稿预览不能当作已确认的员工日程文件。
- 完整历史 Excel 核对导入、应用级跨机备份恢复、不同版本号升级和企业托管设备分发验收。Windows CI 或单个虚拟机离线测试通过，**不等于**客户 UAT 或投产批准。

## Windows 11 x64 安装与工程体验

1. 通过获授权的维护人员获取**经过核实的工程测试安装包**。项目对应提交的 [Windows CI 离线验收工具包](08-RELEASE-HANDBOOK.md#offline-acceptance-kit) 可能供有权限的仓库参与者获取；CI 产物可能过期，**并非正式客户发行版**。不要随意取一个 CI 安装包用于生产。
2. 先按受测构建的 `build.json` 与 SHA-256 核验安装包。当前 `0.1.0` 的 NSIS 工程包常见名称为 `Rigarus Dispatch_0.1.0_x64-setup.exe`；实际文件名和哈希须以相应记录为准。
3. 按获准说明安装；包内带本地 Python sidecar/runtime，并支持在需要时安装随包 WebView2。然后通过 Windows 开始菜单启动 **Rigarus Dispatch**，**不需要软件账号**。

最终用户无需另装 Python、Node.js、Rust 或 .NET 开发环境。特定 Win11 VM 中的无网安装、缺 WebView2 安装及同版本不同构建覆盖升级已有工程通过记录；但代码签名、企业设备策略、不同版本号升级和客户签收仍为独立验收门。详见[安装与验收手册](08-RELEASE-HANDBOOK.md)。

### 合成数据操作示例

1. 打开 **Project Management**，新增虚构 Project 及 Civil/Tower WorkItem（或使用 **Bulk Add Projects**）。
2. 在 **People** 中创建 Crew、员工；按需设置 Foreman 并记录员工可用性。
3. 在 **Schedule → Working calendars** 中明确录入 Crew 和 Project 的 AM/PM 工作日期。
4. 在 **Schedule → Job Schedule** 中点击 **Assign Work Item**，选择 Crew/日期/时段，保存为 **Draft**；前往 **Crew Board** 检查，并试验编辑、明确取消和重启保存。
5. 如有需要，为 Draft 明确指定实际员工并查看 **Employee Week**。它只展示有显式人员关联的任务，并标注 **DRAFT – NOT CONFIRMED**，**不能当作正式派工分发**。

详细步骤见[桌面验收说明](05-DEMO-ACCEPTANCE.md)和[批量输入映射](11-IMPORT-MAPPING.md)。

## 本地数据与隐私

默认数据库位置：

`%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db`

应用日常数据及处理都保留在操作员电脑本地；开发时首次依赖还原、GitHub CI 可以联网。真实客户员工名单、项目地址、原始 Excel/PDF、SQLite 数据库、备份、账号凭据及原始日志，只能保存在获授权的本地环境，不得上传 GitHub 提交、Issue、截图或 CI 产物。

**当前 GitHub 仓库为 Public。** 仓库可公开访问不等于客户数据获授权公开。处理旧数据库前请阅读[数据模型](03-DATA-MODEL.md)和[仓库安全规范](../AGENTS.md)。

## 开发与测试（Windows）

参考[当前 Tauri 源码构建流程](08-RELEASE-HANDBOOK.md#tauri-desktop-preview)准备锁定版本的 Node.js、Rust/MSVC、Python 3.13、uv 及 Windows 工具链。首次下载依赖需要网络。以下命令使用**合成数据**：

```powershell
# 从仓库根目录运行
./scripts/Build-RigarusSidecar.ps1

Push-Location src/Rigarus.Backend
uv sync --locked --group bundle
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked python -m unittest discover -s tests -v
Pop-Location

Push-Location src/Rigarus.Tauri
npm ci
npm run format
npm test
npm run build
npm run tauri -- build -- --locked
Pop-Location
```

历史 **.NET/WPF** 方案仅用于旧版行为和 SQLite 兼容回归，**不是新增功能的技术路线**。如需回归，在仓库根目录运行：

```powershell
dotnet restore Rigarus.sln --locked-mode
dotnet build Rigarus.sln -c Release --no-restore
dotnet test Rigarus.sln -c Release --no-build --no-restore
```

相关文档：[项目规划](00-PROJECT-PLAN.md) · [分阶段交付](09-DELIVERY-PLAYBOOK.md) · [架构](02-ARCHITECTURE.md) · [客户决策登记](10-CLIENT-DECISIONS.md) · [Design-First 开发规范](../AGENTS.md)。

**开发流程：** 一个 Issue → Design-First 核对 → 独立分支 → 自动化/Windows 检查 → **Draft PR 等待人工审核**。不自动合并、发布 Release、关闭 Issue，不能把工程测试当作客户签收。
