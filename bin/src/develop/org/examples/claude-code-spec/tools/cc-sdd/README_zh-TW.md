# cc-sdd

✨ **將 Claude Code/Gemini CLI 從原型開發轉型為生產級開發**

<!-- npm badges -->
[![npm version](https://img.shields.io/npm/v/cc-sdd?logo=npm)](https://www.npmjs.com/package/cc-sdd?activeTab=readme)
[![npm downloads](https://img.shields.io/npm/dm/cc-sdd?logo=npm)](https://www.npmjs.com/package/cc-sdd)
[![install size](https://packagephobia.com/badge?p=cc-sdd)](https://packagephobia.com/result?p=cc-sdd)
[![license: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

<div align="center"><sub>
<a href="./README.md">English</a> | <a href="./README_ja.md">日本語</a> | 繁體中文
</sub></div>

將 **AI-DLC (AI 驅動開發生命週期)** 帶入 Claude Code 與 Gemini CLI。**AI 原生流程**與**最小限的人類批准關卡**：AI 驅動執行，人類在各階段驗證關鍵決策。

🎯 **最佳用途**：脱離傳統開發 70% 的額外負擔（會議、文件、儀式），透過 AI 原生執行和人類品質關卡實現 **從週到小時的交付**。

> **Kiro 相容** — 專業環境中使用的相同實證工作流程。

## 🚀 安裝

```bash
# 基本安裝（預設：英文文件，Claude Code 代理）
npx cc-sdd@latest

# 語言選項（預設：--lang en）
npx cc-sdd@latest --lang zh-TW # 繁體中文
npx cc-sdd@latest --lang ja    # 日語

# 代理選項（預設：claude-code）
npx cc-sdd@latest --gemini-cli --lang zh-TW # Gemini CLI 用
```

## ✨ 快速示範

```bash
# 啟動 AI 代理：'claude' 或 'gemini'

# AI-DLC 核心模式實踐：
/kiro:spec-init 使用 OAuth 建構使用者認證系統  # AI 建立計劃
/kiro:spec-requirements auth-system                 # AI 提出澄清問題
/kiro:spec-design auth-system                      # 人類驗證，AI 實作
/kiro:spec-tasks auth-system                       # 重複：計劃→提問→驗證→實作
```

**30 秒設定** → **AI 驅動「快速衝刺」（非衝刺）** → **小時交付結果**

## ✨ 主要功能

- **🚀 AI-DLC 方法論** - 具人類批准的 AI 原生流程。核心模式：AI 執行，人類驗證
- **📋 規格優先開發** - 全面性規格作為唱一信息源驅動整個生命週期
- **⚡ 「快速衝刺」非衝刺** - 小時/天周期而非周。脱離 70% 管理額外負擔
- **🧠 專案記憶** - AI 在會話間維持持久上下文，學習您的模式
- **🔄 AI 原生+人類關卡** - AI 計劃 → AI 提問 → 人類驗證 → AI 實作（具品質控制的快速循環）
- **🌍 團隊就緒** - 具品質關卡的多語言、跨平台、標準化工作流程

## 🤖 支援的 AI 代理

| 代理 | 狀態 | 指令 | 設定 |
|------|------|------|------|
| **Claude Code** | ✅ 完全支援 | 8 個斜線指令 | `CLAUDE.md` |
| **Gemini CLI** | ✅ 完全支援 | 8 個指令 | `GEMINI.md` |
| 其他 | 📅 規劃中 | - | - |

## 📋 核心指令

### 開發工作流程
```bash
/kiro:spec-init <description>             # 初始化功能規格
/kiro:spec-requirements <feature_name>    # 產生需求
/kiro:spec-design <feature_name>          # 建立技術設計
/kiro:spec-tasks <feature_name>           # 分解為實作任務
/kiro:spec-impl <feature_name> <tasks>    # 以 TDD 執行
/kiro:spec-status <feature_name>          # 檢查進度
```

### 專案設定
```bash
/kiro:steering                            # 建立/更新專案記憶
/kiro:steering-custom                     # 自訂指導規則
```

## ⚙️ 設定

```bash
# 語言與平台
npx cc-sdd@latest --lang zh-TW --os mac    # macOS
npx cc-sdd@latest --lang zh-TW --os linux  # Linux（與 mac 共用模板）
npx cc-sdd@latest --lang zh-TW --os windows # Windows（專用模板）

# 安全操作
npx cc-sdd@latest --dry-run --backup

# 自訂目錄
npx cc-sdd@latest --kiro-dir docs/specs
```

## 📁 專案結構

安裝後，專案將新增：

```
project/
├── .claude/commands/kiro/    # 8 個斜線指令
├── .kiro/specs/             # 功能規格文件
├── .kiro/steering/          # AI 指導規則
└── CLAUDE.md                # 專案設定
```

## 📚 文件與支援

- **[完整文件](https://github.com/gotalab/claude-code-spec/blob/main/README.md)** - 完整設定指南
- **[指令參考](https://github.com/gotalab/claude-code-spec/docs)** - 所有選項與範例
- **[問題與支援](https://github.com/gotalab/claude-code-spec/issues)** - 問題回報與提問
- **[Kiro IDE 整合](https://kiro.dev)** - 進階規格管理

---

**Beta 版本** - 可用且持續改進中。[回報問題](https://github.com/gotalab/claude-code-spec/issues) | MIT License

### 平台支援
- 支援 OS：macOS / Linux / Windows（預設自動偵測）。
- Linux 與 macOS 使用相同的指令模板；Windows 使用專用模板。
