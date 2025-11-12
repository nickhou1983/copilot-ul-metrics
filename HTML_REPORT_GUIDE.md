# GitHub Copilot Metrics HTML 报告使用指南

## 功能概述

现在脚本支持生成美观的 HTML 可视化报告，让您能够更直观地查看 GitHub Copilot 的使用情况。

## 使用方法

### 1. 仅生成 HTML 报告（默认）

```bash
python3 json_to_csv.py your_data.json
```

或明确指定：

```bash
python3 json_to_csv.py your_data.json -t html
```

**输出**：
- `your_data_report.html` - 可视化 HTML 报告

---

### 2. 生成所有文件（8个CSV + 1个HTML）

```bash
python3 json_to_csv.py your_data.json -t all
```

**输出**：
- `your_data_user_summary.csv` - 用户总体指标
- `your_data_by_ide.csv` - IDE 维度统计
- `your_data_by_feature.csv` - 功能维度统计
- `your_data_by_language_feature.csv` - 编程语言+功能统计
- `your_data_by_language_model.csv` - 编程语言+模型统计
- `your_data_by_model_feature.csv` - 模型+功能统计
- `your_data_code_completion_summary.csv` - Code Completion 专项统计
- `your_data_chat_loc_summary.csv` - Chat 代码行数统计
- `your_data_report.html` - 可视化 HTML 报告

---

### 3. 仅生成用户汇总 CSV

```bash
python3 json_to_csv.py your_data.json -t user_summary
```

**输出**：
- `your_data_user_summary.csv` - 用户总体指标

---

### 4. 指定输出目录

```bash
python3 json_to_csv.py your_data.json -o ./reports
```

所有文件将保存在 `./reports` 目录中。

---

## HTML 报告内容

生成的 HTML 报告包含以下部分：

### 📊 整体统计指标

以卡片形式展示 6 个核心指标：

- 🎯 **代码生成总次数** - 所有用户的代码生成次数
- ✅ **代码接受总次数** - 所有用户采纳的代码次数
- 📊 **整体接受率** - 代码接受率百分比
- 📝 **新增代码总行数** - 实际添加的代码行数
- 💬 **用户交互总次数** - 用户主动发起的交互次数
- 💡 **建议代码总行数** - AI 建议的代码行数

### 🎯 功能采用情况

统计不同功能的使用情况：

- 使用 Agent 的用户数及占比
- 使用 Chat 的用户数及占比
- 同时使用两者的用户数
- 仅使用 Code Completion 的用户数

### 🏆 TOP 15 最活跃用户

以表格形式展示最活跃的 15 位用户：

- 排名（🥇🥈🥉前三名有特殊标识）
- 用户名和使用的功能标签（Agent/Chat）
- 代码生成次数
- 代码接受次数
- 接受率（带进度条可视化）
- 新增代码行数
- 交互次数

### 💻 IDE 使用统计

按 IDE 类型统计使用情况：

- IDE 名称（VS Code、IntelliJ、PyCharm 等）
- 使用该 IDE 的用户数
- 代码生成次数
- 代码接受次数
- 接受率（带进度条）
- 新增代码行数

### 🔤 编程语言统计（TOP 10）

展示最常用的 10 种编程语言：

- 语言名称
- 代码生成次数
- 代码接受次数
- 接受率（带进度条）
- 新增代码行数

---

## 报告特点

### 🎨 精美设计

- 渐变色卡片设计
- 动态悬停效果
- 响应式布局，适配各种屏幕尺寸
- 专业的表格样式

### 📊 数据可视化

- 进度条展示接受率
- 颜色编码的指标卡片
- 排名徽章（金、银、铜牌）
- 功能标签（Agent、Chat）

### 🚀 易于分享

- 单个 HTML 文件，无需额外依赖
- 可以通过邮件、网盘等方式分享
- 在任何浏览器中打开即可查看

---

## 示例截图说明

### 整体指标卡片

每个指标用不同颜色的渐变卡片展示，一目了然：
- 蓝色：代码生成
- 绿色：代码接受
- 橙色：接受率
- 红色：代码行数
- 紫色：交互次数

### 用户排行榜

- 前三名有金、银、铜牌标识
- 功能使用标签：蓝色（Agent）、绿色（Chat）
- 接受率以绿色渐变进度条展示

### IDE 和语言统计

以清晰的表格形式展示，每个接受率都有进度条可视化。

---

## 技术细节

### 文件格式

- **编码**：UTF-8
- **大小**：约 25 KB
- **依赖**：无（纯 HTML+CSS）
- **兼容性**：所有现代浏览器

### 样式特性

- **CSS Grid**：响应式网格布局
- **渐变背景**：现代化视觉效果
- **动画效果**：进度条加载动画
- **悬停效果**：交互式卡片

---

## 常见问题

### Q: HTML 报告可以在离线环境查看吗？

**A**: 是的！HTML 报告是完全独立的，不需要网络连接，也不依赖外部资源。

### Q: 报告数据可以更新吗？

**A**: 重新运行脚本即可生成新的报告，每次都会使用最新的数据。

### Q: 可以自定义报告样式吗？

**A**: 可以！报告的所有样式都在 `<style>` 标签中，您可以修改 `json_to_csv.py` 中的 `generate_html_report()` 方法来自定义样式。

### Q: 报告可以打印吗？

**A**: 可以！在浏览器中使用 Ctrl+P（Windows）或 Cmd+P（Mac）打印，建议选择"保存为 PDF"。

### Q: 如何分享报告？

**A**: 直接发送 HTML 文件即可，接收者在浏览器中打开就能查看。

---

## 命令速查表

| 命令 | 说明 | 输出 |
|------|------|------|
| `python3 json_to_csv.py data.json` | 生成 HTML 报告（默认） | 1 个 HTML |
| `python3 json_to_csv.py data.json -t html` | 明确指定生成 HTML | 1 个 HTML |
| `python3 json_to_csv.py data.json -t all` | 生成所有文件 | 8 个 CSV + 1 个 HTML |
| `python3 json_to_csv.py data.json -t user_summary` | 仅生成用户汇总 | 1 个 CSV |
| `python3 json_to_csv.py data.json -o ./output` | 指定输出目录 | 输出到 ./output |
| `python3 json_to_csv.py data.json -t all -o ./reports` | 生成所有文件到指定目录 | 9 个文件到 ./reports |

---

## 更新日志

### v2.0 (2025-11-12)

- ✨ 新增 HTML 可视化报告生成功能
- 🎨 精美的渐变卡片设计
- 📊 动态进度条展示接受率
- 🏆 TOP 15 用户排行榜
- 💻 IDE 使用统计
- 🔤 编程语言统计
- 🎯 功能采用情况分析
- 📱 响应式设计，支持各种屏幕尺寸

---

## 联系支持

如有问题或建议，请通过项目仓库提交 Issue。

**祝您使用愉快！** 🎉
