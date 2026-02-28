# -*- coding: utf-8 -*-
"""
Project: Fatigue Driving Monitoring Baseline
Module: Automated Data Analysis & Visualization Dashboard
Version: 1.0.0
Author: Boyuan Gu (顾博元)

Description:
    A robust tool for one-click processing of experimental N-back data. 
    It automatically scans the 'results/' directory for the latest session data 
    and generates a high-fidelity fatigue trend report. 

Features:
    - Bilingual chart and console support (English/Chinese).
    - Three-panel visualization: Performance (Acc), Alertness (RT), and Subjective (KSS).
    - Intelligent mock-data fallback for demonstration without real data.
    - Professional-grade plot styling using Seaborn.
"""

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import random
import argparse

# ==================== 1. 多语言配置 (i18n) ====================
LANG_CONFIG = {
    'zh': {
        'msg_latest': "✅ 自动定位到最新 N-back 数据文件: {}",
        'msg_no_data': "⚠️ 提示: 本地未检测到真实的 N-back 实验数据。",
        'msg_mocking': "💡 正在生成模拟数据 (Mock Data) 用于演示图表效果...\n",
        'msg_fail': "❌ 错误：读取到的 CSV 缺少必要的字段。自动降级为模拟数据。",
        'msg_save': "✅ 疲劳报告图表已成功生成并保存至:\n   -> {}",
        'chart_main_title': "宇宙管制中心 · 疲劳诱导状态报告\n(受试者: {} | 难度: {})",
        'chart_1_title': "1. 认知表现：监控准确率变化",
        'chart_1_y': "准确率 Accuracy (%)",
        'chart_2_title': "2. 警觉水平：正确反应时 (RT) 变化",
        'chart_2_y': "平均反应时 RT (ms)",
        'chart_3_title': "3. 主观感受：KSS 疲劳度评分攀升",
        'chart_3_y': "KSS 评分 (1-9)",
        'chart_x': "任务区块 (Block)",
        'mock_sub': "演示用户",
        'mock_diff': "NORMAL (模拟)"
    },
    'en': {
        'msg_latest': "✅ Located latest N-back data file: {}",
        'msg_no_data': "⚠️ Note: No real N-back experimental data found.",
        'msg_mocking': "💡 Generating Mock Data to demonstrate dashboard features...\n",
        'msg_fail': "❌ Error: CSV missing required fields. Falling back to Mock Data.",
        'msg_save': "✅ Fatigue report successfully generated and saved to:\n   -> {}",
        'chart_main_title': "Fatigue Induction Status Report\n(Subject: {} | Difficulty: {})",
        'chart_1_title': "1. Performance: Monitoring Accuracy",
        'chart_1_y': "Accuracy (%)",
        'chart_2_title': "2. Vigilance: Response Time (RT) Trend",
        'chart_2_y': "Mean RT (ms)",
        'chart_3_title': "3. Subjective: KSS Sleepiness Progression",
        'chart_3_y': "KSS Rating (1-9)",
        'chart_x': "Task Block",
        'mock_sub': "Demo_User",
        'mock_diff': "NORMAL (Mock)"
    }
}

# ---------------------- Visual Helpers ---------------------- #

def set_chinese_font():
    """Configure Matplotlib for proper multi-language font rendering."""
    system = platform.system()
    if system == "Windows": font_name = "Microsoft YaHei"
    elif system == "Darwin": font_name = "Arial Unicode MS"
    else: font_name = "WenQuanYi Micro Hei"
    plt.rcParams['font.sans-serif'] = [font_name, 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False

def generate_mock_data(L):
    """Generate realistic-looking fatigue data if no real data exists."""
    data = []
    for block in range(1, 7):
        base_acc = 0.95 - (block - 1) * 0.08      
        base_rt = 450 + (block - 1) * 40          
        kss = min(9, 2 + int((block - 1) * 1.3))  
        for trial in range(1, 61):
            correct = 1 if random.random() < base_acc else 0
            rt = base_rt + random.gauss(0, 50) if correct else -1
            data.append({
                'subject_id': L['mock_sub'], 'session': 'Mock', 'difficulty': L['mock_diff'],
                'is_practice': 0, 'block': block, 'trial': trial, 'correct': correct,
                'rt': max(100, rt), 'kss': kss
            })
    return pd.DataFrame(data)

def get_latest_csv(results_dir="results"):
    if not os.path.exists(results_dir): return None
    csv_files = glob.glob(os.path.join(results_dir, "**", "*.csv"), recursive=True)
    npack_files = [f for f in csv_files if "PVT" not in f]
    if not npack_files: return None
    return max(npack_files, key=os.path.getmtime)

# ---------------------- Main Analysis Logic ---------------------- #

def generate_fatigue_report(df, L, save_name="Fatigue_Report.png"):
    # Data Filtering
    sub_id = df['subject_id'].iloc[0] if 'subject_id' in df.columns else "Unknown"
    diff = df['difficulty'].iloc[0] if 'difficulty' in df.columns else "Unknown"
    df_real = df[df['is_practice'] == 0].copy() if 'is_practice' in df.columns else df.copy()

    # Metrics Calculation
    acc_trend = df_real.groupby('block')['correct'].mean() * 100
    rt_trend = df_real[(df_real['correct'] == 1) & (df_real['rt'] > 0)].groupby('block')['rt'].mean()
    kss_trend = df_real.groupby('block')['kss'].first()

    # Plotting
    set_chinese_font()
    sns.set_theme(style="whitegrid", font=plt.rcParams['font.sans-serif'][0])
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle(L['chart_main_title'].format(sub_id, diff), fontsize=16, fontweight='bold', y=1.05)

    # 1. Accuracy Plot
    sns.lineplot(ax=axes[0], x=acc_trend.index, y=acc_trend.values, marker='o', color='#2ecc71', linewidth=2.5)
    axes[0].set_title(L['chart_1_title'], fontsize=13); axes[0].set_ylabel(L['chart_1_y'])
    axes[0].set_ylim(max(0, acc_trend.min() - 10), 105)

    # 2. Response Time Plot
    sns.lineplot(ax=axes[1], x=rt_trend.index, y=rt_trend.values, marker='s', color='#e74c3c', linewidth=2.5)
    axes[1].set_title(L['chart_2_title'], fontsize=13); axes[1].set_ylabel(L['chart_2_y'])

    # 3. KSS Plot
    sns.barplot(ax=axes[2], x=kss_trend.index, y=kss_trend.values, palette="YlOrRd", hue=kss_trend.index, legend=False)
    sns.lineplot(ax=axes[2], x=range(len(kss_trend)), y=kss_trend.values, color='black', alpha=0.3, linestyle='--')
    axes[2].set_title(L['chart_3_title'], fontsize=13); axes[2].set_ylabel(L['chart_3_y']); axes[2].set_ylim(1, 9)

    for ax in axes:
        ax.set_xlabel(L['chart_x'])
        ax.set_xticks(acc_trend.index)

    plt.tight_layout()
    plt.savefig(save_name, dpi=300, bbox_inches='tight')
    print(L['msg_save'].format(save_name))
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", type=str, default='zh', choices=['zh', 'en'], help="Language: zh or en")
    args = parser.parse_args()
    L = LANG_CONFIG[args.lang]

    latest_csv_path = get_latest_csv()
    
    if latest_csv_path:
        print(L['msg_latest'].format(latest_csv_path))
        try:
            df = pd.read_csv(latest_csv_path)
            if 'block' in df.columns and 'kss' in df.columns:
                out_name = latest_csv_path.replace(".csv", f"_Report_{args.lang}.png")
                generate_fatigue_report(df, L, save_name=out_name)
            else:
                print(L['msg_fail'])
                df_mock = generate_mock_data(L)
                generate_fatigue_report(df_mock, L, save_name=f"Mock_Report_{args.lang}.png")
        except Exception as e:
            print(f"Error reading data: {e}")
    else:
        print(L['msg_no_data'])
        print(L['msg_mocking'])
        df_mock = generate_mock_data(L)
        generate_fatigue_report(df_mock, L, save_name=f"Mock_Report_{args.lang}.png")