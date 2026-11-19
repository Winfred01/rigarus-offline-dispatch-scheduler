# Rigarus 离线调度排班工具

[English](../README.md) · 简体中文

Rigarus 是一款供单人使用的 Windows 桌面调度工具，优先支持 Windows 11 x64。软件界面使用英文，安装和日常使用可全程断网，无需登录账号或连接外部服务。项目采用 Tauri、React/TypeScript 和随应用打包的 Python FastAPI 服务，数据保存在本机 SQLite。

## 安装与启动

1. 从获准的交付渠道获取 `Rigarus-Dispatch-x64-setup.exe`。项目成员可按[离线验收包说明](08-RELEASE-HANDBOOK.md#offline-acceptance-kit)获取私有 GitHub Actions 中的内部测试安装包。
2. 将安装包复制到目标电脑，双击并按提示安装。安装包包含 Python 运行时、SQLite 和 WebView2 离线安装程序。目标电脑缺少 WebView2 时，安装程序会使用随包附带的副本。
3. 安装完成后选中 **Run Rigarus Dispatch**，或从 Windows 开始菜单打开 **Rigarus Dispatch**。

使用者无需另外安装 Python、Node.js、Rust、.NET 或 Visual Studio。现有工程预览供合成数据测试，Demo A 客户签收和正式投产待确认。

## 当前工程预览

- **Dashboard** 显示合成项目 **DEMO-001**。编辑备注并点击 **Save note**，关闭应用后重新打开，可核对上次保存的内容。
- **Projects** 可按项目编号、站点 ID 或站点名称搜索，支持新增和编辑项目及工作项。工作项可记录所需班组数和以半天为单位的工期。
- **Crews** 可新建、搜索、编辑、停用和重新启用 Civil（土建）与 Tower（塔架）班组。停用的班组仍可查看。

- **Employees** 可维护员工姓名、所属班组、技能等级、工头资格和启停状态。司机资格默认为未核实。
- **Rigs** 可维护唯一车辆编号、类型、备注、可选默认班组和启停状态。停用后仍保留原编号和记录。

工头任命、排班、导入导出及备份恢复的交付顺序见[项目计划](00-PROJECT-PLAN.md)。

## 本地数据与源码开发

数据库默认位于 `%LOCALAPPDATA%\RigarusDispatch\data\rigarus.db`。开发、演示和 CI 使用合成数据。客户数据库、原始表格、附件、备份和原始诊断日志保存在获准的本地环境。

开发者可按[Windows 源码构建与打包说明](08-RELEASE-HANDBOOK.md#tauri-desktop-preview)准备 Node.js、Rust、Windows C++ 工具链及 Python。首次还原依赖需要联网。仓库中的 .NET/WPF 版本用于核对旧版行为与数据兼容。旧版构建步骤见[英文 README](../README.md#legacy-wpf-development-build)。

- [桌面验收步骤](05-DEMO-ACCEPTANCE.md)
- [项目架构](02-ARCHITECTURE.md)与[数据库模型](03-DATA-MODEL.md)
- [仓库开发约定](../AGENTS.md)
