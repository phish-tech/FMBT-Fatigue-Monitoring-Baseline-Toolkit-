# -*- coding: utf-8 -*-
"""
Project: Fatigue Driving Monitoring Baseline
Module: Objective Fatigue Assessment (Psychomotor Vigilance Task)
Version: 1.0.0
Author: Boyuan Gu (顾博元)

Description:
    This script implements the gold-standard PVT paradigm for objective fatigue assessment.
    It integrates subjective PIS scoring logic, real-time hardware synchronization via LSL,
    and automated data logging for research purposes.

Features:
    - Bilingual UI support (English/Chinese).
    - Standard vs. Personalized baseline modes.
    - Built-in PIS (Fatigue Score) calculation engine.
    - LSL (Lab Streaming Layer) millisecond hardware sync.
    - Automated CSV data logging to 'results/'.
"""

import argparse
import math
import random
import statistics
import sys
import time
import platform
import os
import csv

try:
    import tkinter as tk
    import tkinter.simpledialog as sd
except Exception as e:
    print("Tkinter not available:", e); sys.exit(1)

# ==================== 1. 多语言配置 (i18n) ====================
LANG_CONFIG = {
    'zh': {
        'title': "PVT 疲劳度客观测试系统 (硬件同步版)",
        'sub_prompt': "请输入受试者编号:",
        'sess_prompt': "请输入组别 (Session):",
        'menu': "请按键选择测试模式：\n\n[ 1 ] 标准基线模式 (使用经验基准)\n[ 2 ] 个性化基线模式 (先采集再实测)\n\n按 [Esc] 退出",
        'intro_base': "个性化基线采集 (共 {} 组)\n\n规则：变绿并听到提示音时按对应 W/A/S/D。\n\n按 [Space] 开始第 {} 组基线。",
        'intro_test': "{}\n接下来进行正式疲劳度测试 ({} 分钟)\n\n按 [Space] 开始测试。",
        'base_loaded': "标准基准已加载。",
        'base_done': "个性化基准建立完成！",
        'waiting': "等待中...\n保持专注，不要提前按键",
        'press': "按下 {}!",
        'fs': "抢答 (False Start)!",
        'block_mid': "第 {} 组完成，请稍事休息。\n按 [Space] 开始第 {} 组。",
        'report_title': "========== 疲劳度测试报告 ==========",
        'stats': "按键数: {} | 错键: {} | 抢答: {}",
        'result_label': "评估结果: {}",
        'save_hint': "(数据已自动保存至 results/PVT_Data)",
        'exit_hint': "按 [Esc] 退出",
        'modes': ["基线采集", "正式实测"]
    },
    'en': {
        'title': "Unified PVT Fatigue Assessment (Hardware Sync)",
        'sub_prompt': "Enter Subject ID:",
        'sess_prompt': "Enter Session ID:",
        'menu': "Select Test Mode:\n\n[ 1 ] Standard Baseline (Group Norms)\n[ 2 ] Personal Baseline (Calibration + Test)\n\nPress [Esc] to Exit",
        'intro_base': "Baseline Calibration ({} Blocks)\n\nRule: Press W/A/S/D when screen turns green.\n\nPress [Space] to start Block {}.",
        'intro_test': "{}\nStarting formal fatigue test ({} min).\n\nPress [Space] to start.",
        'base_loaded': "Standard norms loaded.",
        'base_done': "Personal baseline established.",
        'waiting': "Waiting...\nStay focused, do not press early",
        'press': "Press {}!",
        'fs': "False Start!",
        'block_mid': "Block {} complete. Take a break.\nPress [Space] to start Block {}.",
        'report_title': "========== Fatigue Test Report ==========",
        'stats': "Trials: {} | Wrong: {} | FS: {}",
        'result_label': "Rating: {}",
        'save_hint': "(Data saved to results/PVT_Data)",
        'exit_hint': "Press [Esc] to Exit",
        'modes': ["Baseline", "Formal Test"]
    }
}

# ==================== 2. LSL 硬件同步模块 ====================
try:
    from pylsl import StreamInfo, StreamOutlet
    LSL_AVAILABLE = True
except ImportError:
    LSL_AVAILABLE = False

class MarkerStream:
    def __init__(self, name="PVT_Markers", type="Markers"):
        self.active = False
        if LSL_AVAILABLE:
            info = StreamInfo(name, type, 1, 0, 'string', 'pvt_uid_12345')
            self.outlet = StreamOutlet(info)
            self.active = True
            print(f"[LSL] Stream '{name}' established.")
        else:
            print("[LSL] pylsl not found. Hardware sync disabled.")

    def push(self, marker_str):
        if self.active: self.outlet.push_sample([marker_str])

# ---------------------- Defaults ----------------------
DEF_ISI_MIN_MS     = 2000
DEF_ISI_MAX_MS     = 10000
DEF_LAPSE_MS       = 500
DEF_PENALTY_MS     = 200     
DEF_FONT           = ("Microsoft YaHei", 20, "bold") 
DEF_N_BASE_BLOCKS  = 3       
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "results", "PVT_Data")

STD_BASELINE = {
    'mu_speed': 1.50,  'sigma_speed': 0.15,
    'mu_lapse': 8.00,  'sigma_lapse': 1.00,
    'mu_fs': 0.10,     'sigma_fs': 0.10
}

# ---------------------- Helpers ----------------------
def ms(x): return int(round(x * 1000.0))

def play_sound():
    try:
        if platform.system() == "Windows":
            import winsound; winsound.Beep(800, 150)
        elif platform.system() == "Darwin":
            os.system("afplay /System/Library/Sounds/Ping.aiff &")
    except Exception: pass

def compute_summary(rows, duration_sec, false_starts):
    valid_rts = [r["rt_ms_eff"] for r in rows if (not r.get("is_false_start", False)) and r.get("rt_ms_eff") is not None]
    lapses = sum(1 for r in rows if r.get("is_lapse", False))
    duration_min = max(duration_sec / 60.0, 1e-6)
    inv_rts = [1000.0 / rt for rt in valid_rts if rt > 0]
    return dict(
        mean_speed=statistics.mean(inv_rts) if inv_rts else 0.0,
        lapses_per_min=lapses / duration_min,
        fs_per_min=false_starts / duration_min,
        n_trials=len([r for r in rows if r.get("rt_ms") is not None]),
        wrongs=sum(1 for r in rows if r.get("wrong_key", False))
    )

def calculate_pis_score(test_stats, baseline):
    z_speed = (test_stats['mean_speed'] - baseline['mu_speed']) / max(baseline['sigma_speed'], 1e-5)
    z_lapse = (test_stats['lapses_per_min'] - baseline['mu_lapse']) / max(baseline['sigma_lapse'], 1e-5)
    z_fs    = (test_stats['fs_per_min'] - baseline['mu_fs']) / max(baseline['sigma_fs'], 1e-5)
    pis_score = (-z_speed + z_lapse + 0.5 * z_fs) / 2.5
    return pis_score

# ---------------------- GUI App ----------------------
class UnifiedPVTApp:
    def __init__(self, args, sub_id, session):
        self.args, self.sub_id, self.session = args, sub_id, session
        self.L = LANG_CONFIG[args.lang]
        self.root = tk.Tk()
        self.root.title(self.L['title'])
        self.root.geometry("900x600")
        self.root.configure(bg="black")
        self.root.bind("<Key>", self.on_key)

        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.label = tk.Label(self.canvas, text="", fg="white", bg="black", font=DEF_FONT, justify="center")
        self.label.place(relx=0.5, rely=0.5, anchor="center")

        self.state, self.mode, self.baseline = "menu", None, None
        self.rows, self.all_data = [], []
        self.false_starts = 0
        self.session_start = self.stim_time = self.required_key = None
        self.after_target_id = self.after_flash_id = None
        self.base_summaries = []
        self.current_base_block = 1

        self.marker = MarkerStream("PVT_Markers")
        self.show_menu()

    def set_text(self, text, color="white", bg="black"):
        self.canvas.configure(bg=bg); self.label.configure(text=text, fg=color, bg=bg)

    def flash_message(self, text, fg="white", bg="black", ms_dur=300):
        self.set_text(text, color=fg, bg=bg)
        if self.after_flash_id: self.root.after_cancel(self.after_flash_id)
        self.after_flash_id = self.root.after(ms_dur, lambda: self.set_text("...", color="white", bg="black"))

    def show_menu(self):
        self.state = "menu"
        self.set_text(f"{self.L['title']} - ID: {self.sub_id}\n\n{self.L['menu']}")

    def show_intro_base(self):
        self.state = "intro_base"
        self.set_text(self.L['intro_base'].format(DEF_N_BASE_BLOCKS, self.current_base_block))

    def show_intro_test(self):
        self.state = "intro_test"
        prefix = self.L['base_loaded'] if self.mode == 'standard' else self.L['base_done']
        self.set_text(self.L['intro_test'].format(prefix, self.args.duration_min))

    def start_block(self, is_test=False):
        self.state = "run_test" if is_test else "run_base"
        self.rows, self.false_starts, self.session_start = [], 0, time.perf_counter()
        self.marker.push(f"Block_Start_{'Test' if is_test else 'Base'}")
        self.schedule_next_trial()

    def schedule_next_trial(self):
        elapsed = time.perf_counter() - self.session_start
        if elapsed >= self.args.duration_min * 60.0:
            if self.state == "run_test": self.finish_test()
            else: self.finish_base_block()
            return
        isi_ms = random.randint(self.args.isi_min_ms, self.args.isi_max_ms)
        self.required_key = None
        mode_str = self.L['modes'][1] if self.state == "run_test" else f"{self.L['modes'][0]} ({self.current_base_block}/{DEF_N_BASE_BLOCKS})"
        self.set_text(f"{mode_str}\n\n{self.L['waiting']}", color="gray", bg="black")
        if self.after_target_id: self.root.after_cancel(self.after_target_id)
        self.after_target_id = self.root.after(isi_ms, self.show_target)

    def show_target(self):
        self.stim_time, self.required_key = time.perf_counter(), random.choice(["w","a","s","d"])
        self.marker.push(f"Target_Show_{self.required_key.upper()}")
        self.set_text(self.L['press'].format(self.required_key.upper()), color="black", bg="lime"); play_sound()

    def on_key(self, event):
        if event.keysym == "Escape": self.root.destroy(); return
        key_lower = event.keysym.lower()
        if self.state == "menu":
            if event.keysym == "1": self.mode = "standard"; self.baseline = STD_BASELINE; self.show_intro_test()
            elif event.keysym == "2": self.mode = "personal"; self.show_intro_base()
            return
        if event.keysym == "space":
            if self.state == "intro_base": self.start_block(is_test=False)
            elif self.state == "intro_test": self.start_block(is_test=True)
            elif self.state in ("between_base", "between"): self.start_block(is_test=False)
            return
        if self.state in ["run_base", "run_test"]:
            if self.required_key is None:
                self.false_starts += 1; self.marker.push("False_Start"); self.flash_message(self.L['fs'], fg="yellow", bg="darkred", ms_dur=400)
                self.all_data.append({'subject_id': self.sub_id, 'session': self.session, 'mode': self.state, 'trial_type': 'FalseStart', 'rt_ms': -1, 'rt_ms_eff': -1, 'is_lapse': False, 'wrong_key': False})
            else: self.register_response(key_lower)

    def register_response(self, key_lower):
        rt_ms = ms(time.perf_counter() - self.stim_time)
        wrong_key = (key_lower != self.required_key)
        rt_eff = rt_ms + (self.args.penalty_ms if wrong_key else 0)
        self.marker.push(f"Resp_{'Wrong' if wrong_key else 'Correct'}_RT_{rt_ms}")
        
        trial_data = {'subject_id': self.sub_id, 'session': self.session, 'mode': self.state, 'trial_type': 'Normal', 'rt_ms': rt_ms, 'rt_ms_eff': rt_eff, 'is_lapse': (rt_eff >= self.args.lapse_ms), 'wrong_key': wrong_key}
        self.rows.append(trial_data); self.all_data.append(trial_data)
        
        msg = f"RT: {rt_ms} ms" + (f" +{self.args.penalty_ms}ms" if wrong_key else "")
        self.required_key = None; self.flash_message(msg, ms_dur=300); self.schedule_next_trial()

    def finish_base_block(self):
        if self.after_target_id: self.root.after_cancel(self.after_target_id)
        if self.after_flash_id: self.root.after_cancel(self.after_flash_id)
        self.marker.push("Block_End_Base")
        self.base_summaries.append(compute_summary(self.rows, time.perf_counter() - self.session_start, self.false_starts))

        if self.current_base_block < DEF_N_BASE_BLOCKS:
            self.state = "between"; self.current_base_block += 1
            self.set_text(self.L['block_mid'].format(self.current_base_block-1, self.current_base_block))
        else:
            speeds = [s['mean_speed'] for s in self.base_summaries]; lapses = [s['lapses_per_min'] for s in self.base_summaries]; fss = [s['fs_per_min'] for s in self.base_summaries]
            self.baseline = {'mu_speed': statistics.mean(speeds), 'sigma_speed': statistics.stdev(speeds) if len(speeds)>1 else 0.1, 'mu_lapse': statistics.mean(lapses), 'sigma_lapse': statistics.stdev(lapses) if len(lapses)>1 else 0.1, 'mu_fs': statistics.mean(fss), 'sigma_fs': statistics.stdev(fss) if len(fss)>1 else 0.1}
            self.show_intro_test()

    def finish_test(self):
        if self.after_target_id: self.root.after_cancel(self.after_target_id)
        if self.after_flash_id: self.root.after_cancel(self.after_flash_id)
        self.marker.push("Block_End_Test")
        
        # Save Data
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        csv_path = os.path.join(OUTPUT_DIR, f"{self.sub_id}_{self.session}_PVT_{time.strftime('%Y%m%d_%H%M%S')}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['subject_id', 'session', 'mode', 'trial_type', 'rt_ms', 'rt_ms_eff', 'is_lapse', 'wrong_key'])
            writer.writeheader(); writer.writerows(self.all_data)
        
        test_stats = compute_summary(self.rows, time.perf_counter() - self.session_start, self.false_starts)
        score = calculate_pis_score(test_stats, self.baseline)
        
        # Level Logic
        if score < 0.5: desc = "Alert / Level 0" if self.args.lang == 'en' else "0 档 (清醒 / 低疲劳)"
        elif score < 1.0: desc = "Mild / Level 1" if self.args.lang == 'en' else "1 档 (中度疲劳)"
        else: desc = "Fatigued / Level 2" if self.args.lang == 'en' else "2 档 (重度疲劳)"

        report = f"{self.L['report_title']}\n\n{self.L['stats'].format(test_stats['n_trials'], test_stats['wrongs'], self.false_starts)}\n\n{self.L['result_label'].format(desc)}\n\n{self.L['save_hint']}\n\n{self.L['exit_hint']}"
        self.set_text(report); self.state = "done"

# ---------------------- Main ----------------------
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--lang", type=str, default='zh', choices=['zh', 'en'], help="Language: zh or en")
    p.add_argument("--duration_min", type=float, default=3.0, help="Test duration in minutes")
    p.add_argument("--isi_min_ms", type=int, default=2000)
    p.add_argument("--isi_max_ms", type=int, default=5000)
    p.add_argument("--lapse_ms", type=int, default=500)
    p.add_argument("--penalty_ms", type=int, default=200)
    args = p.parse_args()
    
    # Subject Info Dialog
    root = tk.Tk(); root.withdraw()
    L = LANG_CONFIG[args.lang]
    sub_id = sd.askstring("Input", L['sub_prompt'], initialvalue="Sub01")
    session = sd.askstring("Input", L['sess_prompt'], initialvalue="01")
    root.destroy()
    
    if sub_id:
        app = UnifiedPVTApp(args, sub_id, session)
        app.root.mainloop()