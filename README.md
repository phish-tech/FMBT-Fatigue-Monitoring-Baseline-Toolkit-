# Fatigue Monitoring Baseline Toolkit (FMBT)
## 疲劳驾驶监测科研基准工具包

[![Language](https://img.shields.io/badge/Language-English%20%2F%20%E4%B8%AD%E6%96%87-blue.svg)](#bilingual-support)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 📖 Project Overview / 项目简介

**FMBT** is a high-performance, research-oriented toolkit designed for fatigue-related studies, specifically tailored as a baseline for **belt-based fatigue monitoring systems**. It provides a closed-loop workflow: from rapid mental fatigue induction to objective assessment and automated data analysis.

**FMBT** 是一套专为疲劳研究设计的科研工具包，特别适用于作为**基于安全带的疲劳监测系统**的对比基准（Baseline）。它提供了一套完整的闭环工作流：从快速脑力疲劳诱导，到客观疲劳度评估，再到全自动化的数据分析。

---

## 🛠️ Core Modules / 核心模块

### 1. Objective Assessment / 客观评估: `fatigue_pvt.py`
Based on the **Psychomotor Vigilance Task (PVT)**, the gold standard for measuring vigilance.
* **Bilingual Support**: Full English and Chinese UI support.
* **Modes**: Supports both "Standard Norms" (using pre-set population data) and "Personalized Baseline" calibration (captures 3 blocks of user data).
* **PIS Scoring**: Built-in Fatigue Score (PIS) engine based on Z-score normalization of mean speed, lapses, and false starts.
* **Hardware Sync**: Integrated LSL (Lab Streaming Layer) for millisecond-level event marking.

基于警觉性测试金标准 —— **精神运动警觉性任务 (PVT)**。
* **双语支持**：UI 界面完整支持中英文切换。
* **测试模式**：支持“标准常模”（使用人群经验数据）和“个性化基线标定”（通过 3 组测试建立个人模型）两种模式。
* **PIS 评分**：内置 PIS 疲劳度算法，综合速度、迟钝（Lapses）和抢答（False Starts）的 Z 分数进行疲劳等级判定。
* **硬件同步**：内置 LSL (Lab Streaming Layer) 接口，实现毫秒级硬件打标同步。

### 2. Rapid Induction / 快速诱导: `n_back_induction.py`
Rapidly induces mental fatigue within 15 minutes through high-intensity working memory tasks.
* **Gamified Experience**: Packaged as a "Space Control Center" mission with high-quality Sci-Fi UI to maintain subject engagement.
* **Visual Feedback**: Procedural "Data Core" visuals that degrade (pixelate) as the subject's accuracy drops.
* **Difficulty Tiers**: Three levels (EASY/NORMAL/HARD) adjusting N-back depth (2-back/3-back) and stimulus speed.
* **Built-in KSS**: Seamlessly integrates the Karolinska Sleepiness Scale (1-9) for subjective monitoring.

通过高强度的工作记忆刷新任务，在 15 分钟内快速诱发脑部疲劳。
* **游戏化体验**：采用“宇宙管制中心”科幻背景，有效防止受试者因任务枯燥产生动机减退。
* **视觉反馈**：程序化生成“数据核心”图像，其清晰度会随受试者正确率实时产生像素化降级。
* **难度梯度**：提供三种难度（新手、标准、高压），动态调整 N-back 深度及刺激间隔时间。
* **内置量表**：无缝集成 KSS (Karolinska Sleepiness Scale) 主观疲劳自评量表。

### 3. Automated Dashboard / 自动化仪表盘: `analysis_dashboard.py`
One-click generation of professional-grade research reports.
* **Visual Metrics**: Tracks Accuracy, Reaction Time (RT), and KSS trends across task blocks using Seaborn.
* **Robust Demo Mode**: Automatically generates simulated "Mock Data" for demonstration if no real experimental data is found.

一键生成达到“论文级”美观度的科研数据报告。
* **多维可视化**：利用 Seaborn 自动分析并展示跨区块的准确率、反应时间及 KSS 变化趋势。
* **鲁棒演示模式**：若本地无真实实验数据，将自动生成符合疲劳规律的模拟数据进行功能演示。

---

## 🚀 Quick Start / 快速开始

### Installation / 环境准备
```bash
# Clone the repository
git clone https://github.com/phish-tech/FMBT-Fatigue-Monitoring-Baseline-Toolkit-
cd Fatigue_Driving_Baseline

# Install dependencies
pip install pygame pylsl pandas matplotlib seaborn
```

### Running the Modules / 启动模块

| Module / 功能模块 | Command / 启动命令 |
| :--- | :--- |
| **Fatigue Assessment (PVT)** | `python fatigue_pvt.py --lang en` (English Version) | python fatigue_pvt.py （中文版本）
| **Fatigue Induction (N-back)** | `python n_back_induction.py --lang en` (English Version) | python n_back_induction.py （中文版本）
| **Data Analysis Dashboard** | `python analysis_dashboard.py --lang en` (English Version) | python analysis_dashboard.py（中文版本）

---

## 📡 Hardware Synchronization / 硬件同步说明

This toolkit is designed to sync with hardware sensors (e.g., EEG, ECG, or belt-based strain sensors).
* **LSL Markers**: Both `fatigue_pvt.py` and `n_back_induction.py` broadcast event markers (Stimulus Show, Key Press, False Start, etc.) via LSL.
* **Timestamp Alignment**: Use tools like **LabRecorder** to record both the sensor data stream and the FMBT marker stream for millisecond-accurate alignment.

本工具包专为硬件传感器（如脑电、心电或安全带应变传感器）同步而设计。
* **LSL 打标**：PVT 和 N-back 模块均会通过 LSL 广播事件标签（刺激呈现、按键响应、抢答等）。
* **时间戳对齐**：建议使用 **LabRecorder** 等工具同时记录传感器流与 FMBT 标记流，以实现毫秒级对齐。

---

## ✉️ Author & Signature / 作者与署名

* **Author**: Boyuan Gu (phish_tech)
* **Date**: February 2026
* **License**: MIT
