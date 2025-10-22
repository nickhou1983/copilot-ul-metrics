# GitHub Copilot User Level Metrics - 快速开始

## 🚀 快速上手

### 步骤 1: 转换 JSON 到 CSV

```bash
# 转换 JSON 文件为 CSV（生成所有维度）
python3 json_to_csv.py your_data.json

# 或指定输出目录
python3 json_to_csv.py your_data.json -o ./output
```

这将生成 6 个 CSV 文件：
- ✅ `*_user_summary.csv` - 用户总体指标
- ✅ `*_by_ide.csv` - IDE 维度统计
- ✅ `*_by_feature.csv` - 功能维度统计
- ✅ `*_by_language_feature.csv` - 语言+功能维度
- ✅ `*_by_language_model.csv` - 语言+模型维度
- ✅ `*_by_model_feature.csv` - 模型+功能维度

### 步骤 2: 安装分析工具依赖（可选）

如果需要使用数据分析脚本：

```bash
pip3 install -r requirements.txt
```

### 步骤 3: 运行数据分析

```bash
python3 analyze_metrics.py
```

这将生成完整的分析报告，包括：
- 📊 用户活跃度统计
- 🏆 TOP 10 活跃用户
- ⚡ 各功能使用情况
- 🔤 编程语言分布
- 🛠️ IDE 使用统计
- 🤖 AI 模型效果对比

## 📊 使用 Excel 分析

生成的 CSV 文件可以直接在 Excel 中打开：

1. 双击打开 CSV 文件
2. 使用"插入" > "数据透视表"创建分析视图
3. 创建图表进行可视化

## 🎯 常见使用场景

### 场景 1: 查看特定用户的使用情况

在 Excel 或 Python 中筛选特定的 `user_login`：

```python
import pandas as pd
df = pd.read_csv('*_user_summary.csv')
user_data = df[df['user_login'] == 'username']
print(user_data)
```

### 场景 2: 分析某个日期范围的数据

```python
df['day'] = pd.to_datetime(df['day'])
sept_data = df[(df['day'] >= '2025-09-01') & (df['day'] <= '2025-09-30')]
print(f"9月总代码生成次数: {sept_data['code_generation_activity_count'].sum()}")
```

### 场景 3: 对比不同编程语言的接受率

```python
lang_df = pd.read_csv('*_by_language_feature.csv')
lang_stats = lang_df.groupby('language').agg({
    'code_generation_activity_count': 'sum',
    'code_acceptance_activity_count': 'sum'
})
lang_stats['acceptance_rate'] = (
    lang_stats['code_acceptance_activity_count'] / 
    lang_stats['code_generation_activity_count'] * 100
)
print(lang_stats.sort_values('acceptance_rate', ascending=False))
```

### 场景 4: 分析功能采用趋势

```python
feature_df = pd.read_csv('*_by_feature.csv')
feature_df['day'] = pd.to_datetime(feature_df['day'])
daily_usage = feature_df.groupby(['day', 'feature'])['code_generation_activity_count'].sum().unstack()
daily_usage.plot(kind='line', figsize=(12, 6), title='功能使用趋势')
```

## 📁 项目文件说明

| 文件 | 说明 | 依赖 |
|------|------|------|
| `json_to_csv.py` | JSON 转 CSV 转换器 | 无（仅Python标准库） |
| `analyze_metrics.py` | 数据分析示例脚本 | pandas |
| `requirements.txt` | Python 依赖列表 | - |
| `README.md` | 完整的文档和指标说明 | - |
| `QUICK_START.md` | 本快速入门指南 | - |

## 💡 提示

- CSV 文件使用 UTF-8-BOM 编码，可以在 Excel 中正确显示中文
- `json_to_csv.py` 无需安装任何依赖即可使用
- `analyze_metrics.py` 需要安装 pandas，但提供了更丰富的分析功能
- 所有脚本都支持 `--help` 参数查看详细使用说明

## 🔗 更多信息

详细的指标说明和数据结构请参考 [README.md](README.md)
