#!/usr/bin/env python3
"""
GitHub Copilot Metrics - 数据分析示例
演示如何使用生成的 CSV 文件进行数据分析
"""

import pandas as pd
import glob
from pathlib import Path


def analyze_user_summary(csv_file: str):
    """分析用户总体指标"""
    print("\n" + "=" * 70)
    print("📊 用户总体指标分析")
    print("=" * 70)
    
    df = pd.read_csv(csv_file)
    
    print(f"\n📈 基础统计:")
    print(f"   总用户数: {df['user_id'].nunique()}")
    print(f"   总记录数: {len(df)}")
    print(f"   数据日期范围: {df['day'].min()} 至 {df['day'].max()}")
    
    print(f"\n🎯 活动指标:")
    print(f"   总交互次数: {df['user_initiated_interaction_count'].sum():,}")
    print(f"   总代码生成次数: {df['code_generation_activity_count'].sum():,}")
    print(f"   总代码接受次数: {df['code_acceptance_activity_count'].sum():,}")
    print(f"   平均接受率: {df['acceptance_rate'].mean():.2f}%")
    
    print(f"\n📝 代码行数统计:")
    print(f"   总建议新增行数: {df['loc_suggested_to_add_sum'].sum():,}")
    print(f"   总实际新增行数: {df['loc_added_sum'].sum():,}")
    print(f"   总实际删除行数: {df['loc_deleted_sum'].sum():,}")
    print(f"   平均采纳率: {df['adoption_rate'].mean():.2f}%")
    
    print(f"\n🚀 高级功能采用:")
    agent_users = df['used_agent'].sum()
    chat_users = df['used_chat'].sum()
    total_users = df['user_id'].nunique()
    print(f"   使用 Agent 的记录数: {agent_users} ({agent_users/len(df)*100:.1f}%)")
    print(f"   使用 Chat 的记录数: {chat_users} ({chat_users/len(df)*100:.1f}%)")
    
    print(f"\n🏆 TOP 10 最活跃用户 (按代码生成次数):")
    top_users = df.groupby('user_login').agg({
        'code_generation_activity_count': 'sum',
        'code_acceptance_activity_count': 'sum',
        'loc_added_sum': 'sum'
    }).sort_values('code_generation_activity_count', ascending=False).head(10)
    
    for idx, (user, row) in enumerate(top_users.iterrows(), 1):
        print(f"   {idx:2d}. {user:30s} - 生成: {row['code_generation_activity_count']:4.0f}, "
              f"接受: {row['code_acceptance_activity_count']:4.0f}, "
              f"新增行数: {row['loc_added_sum']:5.0f}")


def analyze_by_feature(csv_file: str):
    """分析功能维度"""
    print("\n" + "=" * 70)
    print("⚡ 功能维度分析")
    print("=" * 70)
    
    df = pd.read_csv(csv_file)
    
    # 按功能聚合
    feature_stats = df.groupby('feature').agg({
        'code_generation_activity_count': 'sum',
        'code_acceptance_activity_count': 'sum',
        'loc_suggested_to_add_sum': 'sum',
        'loc_added_sum': 'sum'
    }).sort_values('code_generation_activity_count', ascending=False)
    
    print(f"\n📊 各功能使用统计:")
    for feature, row in feature_stats.iterrows():
        acceptance_rate = (row['code_acceptance_activity_count'] / row['code_generation_activity_count'] * 100) if row['code_generation_activity_count'] > 0 else 0
        print(f"\n   【{feature}】")
        print(f"      代码生成次数: {row['code_generation_activity_count']:,.0f}")
        print(f"      代码接受次数: {row['code_acceptance_activity_count']:,.0f}")
        print(f"      接受率: {acceptance_rate:.2f}%")
        print(f"      建议新增行数: {row['loc_suggested_to_add_sum']:,.0f}")
        print(f"      实际新增行数: {row['loc_added_sum']:,.0f}")


def analyze_by_language(csv_file: str):
    """分析编程语言维度"""
    print("\n" + "=" * 70)
    print("🔤 编程语言维度分析")
    print("=" * 70)
    
    df = pd.read_csv(csv_file)
    
    # 按语言聚合
    lang_stats = df.groupby('language').agg({
        'code_generation_activity_count': 'sum',
        'code_acceptance_activity_count': 'sum',
        'loc_suggested_to_add_sum': 'sum',
        'loc_added_sum': 'sum'
    }).sort_values('code_generation_activity_count', ascending=False).head(10)
    
    print(f"\n📊 TOP 10 使用最多的编程语言:")
    for idx, (lang, row) in enumerate(lang_stats.iterrows(), 1):
        acceptance_rate = (row['code_acceptance_activity_count'] / row['code_generation_activity_count'] * 100) if row['code_generation_activity_count'] > 0 else 0
        print(f"\n   {idx:2d}. 【{lang}】")
        print(f"       代码生成次数: {row['code_generation_activity_count']:,.0f}")
        print(f"       代码接受次数: {row['code_acceptance_activity_count']:,.0f}")
        print(f"       接受率: {acceptance_rate:.2f}%")
        print(f"       实际新增行数: {row['loc_added_sum']:,.0f}")


def analyze_by_ide(csv_file: str):
    """分析IDE维度"""
    print("\n" + "=" * 70)
    print("🛠️ IDE 维度分析")
    print("=" * 70)
    
    df = pd.read_csv(csv_file)
    
    # 按IDE聚合
    ide_stats = df.groupby('ide').agg({
        'user_initiated_interaction_count': 'sum',
        'code_generation_activity_count': 'sum',
        'code_acceptance_activity_count': 'sum',
        'loc_added_sum': 'sum'
    }).sort_values('code_generation_activity_count', ascending=False)
    
    print(f"\n📊 各 IDE 使用统计:")
    for ide, row in ide_stats.iterrows():
        acceptance_rate = (row['code_acceptance_activity_count'] / row['code_generation_activity_count'] * 100) if row['code_generation_activity_count'] > 0 else 0
        print(f"\n   【{ide.upper()}】")
        print(f"      用户交互次数: {row['user_initiated_interaction_count']:,.0f}")
        print(f"      代码生成次数: {row['code_generation_activity_count']:,.0f}")
        print(f"      代码接受次数: {row['code_acceptance_activity_count']:,.0f}")
        print(f"      接受率: {acceptance_rate:.2f}%")
        print(f"      实际新增行数: {row['loc_added_sum']:,.0f}")


def analyze_by_model(csv_file: str):
    """分析AI模型维度"""
    print("\n" + "=" * 70)
    print("🤖 AI 模型维度分析")
    print("=" * 70)
    
    df = pd.read_csv(csv_file)
    
    # 按模型聚合
    model_stats = df.groupby('model').agg({
        'user_initiated_interaction_count': 'sum',
        'code_generation_activity_count': 'sum',
        'code_acceptance_activity_count': 'sum',
        'loc_suggested_to_add_sum': 'sum',
        'loc_added_sum': 'sum'
    }).sort_values('code_generation_activity_count', ascending=False)
    
    print(f"\n📊 各 AI 模型使用统计:")
    for model, row in model_stats.iterrows():
        acceptance_rate = (row['code_acceptance_activity_count'] / row['code_generation_activity_count'] * 100) if row['code_generation_activity_count'] > 0 else 0
        print(f"\n   【{model}】")
        print(f"      用户交互次数: {row['user_initiated_interaction_count']:,.0f}")
        print(f"      代码生成次数: {row['code_generation_activity_count']:,.0f}")
        print(f"      代码接受次数: {row['code_acceptance_activity_count']:,.0f}")
        print(f"      接受率: {acceptance_rate:.2f}%")
        print(f"      建议新增行数: {row['loc_suggested_to_add_sum']:,.0f}")
        print(f"      实际新增行数: {row['loc_added_sum']:,.0f}")


def main():
    """主函数"""
    print("\n🎯 GitHub Copilot User Level Metrics - 数据分析报告")
    print("=" * 70)
    
    # 查找所有 CSV 文件
    csv_files = glob.glob("*_*.csv")
    
    if not csv_files:
        print("❌ 未找到 CSV 文件，请先运行 json_to_csv.py 生成 CSV 文件")
        return
    
    print(f"\n找到 {len(csv_files)} 个 CSV 文件")
    
    # 分析用户总体指标
    user_summary_files = [f for f in csv_files if '_user_summary.csv' in f]
    if user_summary_files:
        analyze_user_summary(user_summary_files[0])
    
    # 分析功能维度
    feature_files = [f for f in csv_files if '_by_feature.csv' in f]
    if feature_files:
        analyze_by_feature(feature_files[0])
    
    # 分析编程语言维度
    lang_feature_files = [f for f in csv_files if '_by_language_feature.csv' in f]
    if lang_feature_files:
        analyze_by_language(lang_feature_files[0])
    
    # 分析IDE维度
    ide_files = [f for f in csv_files if '_by_ide.csv' in f]
    if ide_files:
        analyze_by_ide(ide_files[0])
    
    # 分析AI模型维度
    model_feature_files = [f for f in csv_files if '_by_model_feature.csv' in f]
    if model_feature_files:
        analyze_by_model(model_feature_files[0])
    
    print("\n" + "=" * 70)
    print("✅ 分析完成！")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
