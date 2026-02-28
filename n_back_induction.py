# -*- coding: utf-8 -*-
"""
Project: Fatigue Driving Monitoring Baseline
Module: Rapid Fatigue Induction (Gamified N-back Task)
Version: 1.0.0
Author: Boyuan Gu (顾博元)

Description:
    A high-intensity N-back task designed to induce mental fatigue within 15 minutes.
    It uses procedural visual feedback to replace external image assets and supports
    millisecond-level hardware synchronization via LSL.

Features:
    - Bilingual UI support (Sci-Fi themed English/Chinese).
    - Procedural "Data Core" visuals (accuracy-based pixelation).
    - 3 Difficulty levels (2-back to high-speed 3-back).
    - Integrated Karolinska Sleepiness Scale (KSS).
    - LSL (Lab Streaming Layer) event marking for hardware sync.
"""

import pygame
import random
import csv
import time
import os
import sys
import math
import platform
import statistics
import argparse

# ==================== 1. 多语言配置 (i18n) ====================
LANG_CONFIG = {
    'zh': {
        'title': "宇宙管制中心 · 硬件同步终端",
        'login_title': "登录宇宙管制终端",
        'sub_label': "被试编号 (Subject ID):",
        'sess_label': "实验组别 (Session):",
        'demo_mode': "仅体验模式 (不保存数据)",
        'enter_btn': "进 入",
        'diff_title': "选择疲劳诱导强度",
        'diff_labels': {"EASY": "新手适应模式", "NORMAL": "标准疲劳诱导", "HARD": "高压极限模式"},
        'hud_core': "核心通信",
        'hud_sector': "扇区",
        'hud_signal': "信号",
        'hud_energy': "区块能量",
        'hud_total': "总调度域",
        'intro_title': "{} 准备启动",
        'rules': "规则协议：若当前字母与 {} 步前【相同】按 J，【不同】按 F",
        'start_hint': "按任意键开始执行...",
        'kss_title': "扇区 {} 完毕 - 疲劳状态自我监控 (KSS)",
        'kss_opts': ["1: 极其清醒", "3: 清醒", "5: 一般状态", "7: 困倦但无需入睡", "9: 极度困倦，难以支撑"],
        'kss_hint': "请指挥官按数字键 1 - 9 输入当前生理状态评估",
        'feedback_title': "第 {}/{} 区块任务结束",
        'feedback_prac': "练习通道结束",
        'stat_acc': "监控正确率：{:.1f}%",
        'stat_rt': "平均反应时：{:.0f} ms",
        'stat_score': "本区块积分：{}",
        'stat_combo': "最高连击：{}",
        'stat_rt_none': "无有效反应",
        'ach_title': "【 本区块评估报告 】",
        'ach_none': "各项指标平稳，请继续保持专注。",
        'mem_title': "核心重构质量检视",
        'mem_status': ["核心解体", "链路不稳定", "运转正常", "完美的同步率！"],
        'cont_hint': "按任意键继续",
        'end_title': "所有诱导区块执行完毕",
        'end_score': "最终总分: {}",
        'end_save': "数据已安全上传至终端",
        'end_demo': "体验模式结束",
        'end_exit': "按任意键断开连接"
    },
    'en': {
        'title': "Space Control Center · Hardware Sync Terminal",
        'login_title': "Access Control Terminal",
        'sub_label': "Subject ID:",
        'sess_label': "Session ID:",
        'demo_mode': "Demo Mode (No Data Logging)",
        'enter_btn': "ACCESS",
        'diff_title': "Select Induction Intensity",
        'diff_labels': {"EASY": "Cadet Orientation", "NORMAL": "Standard Induction", "HARD": "High-Pressure Overload"},
        'hud_core': "Core Link",
        'hud_sector': "Sector",
        'hud_signal': "Signal",
        'hud_energy': "Sector Energy",
        'hud_total': "Command Domain",
        'intro_title': "{} Initializing",
        'rules': "Protocol: Press J if stimulus matches {} steps back, else press F",
        'start_hint': "Press any key to execute...",
        'kss_title': "Sector {} Complete - Fatigue Monitoring (KSS)",
        'kss_opts': ["1: Very Alert", "3: Alert", "5: Neither", "7: Sleepy", "9: Very Sleepy"],
        'kss_hint': "Commander, press 1-9 to input physiological status",
        'feedback_title': "Sector {}/{} Mission End",
        'feedback_prac': "Practice Channel Closed",
        'stat_acc': "Sync Accuracy: {:.1f}%",
        'stat_rt': "Mean RT: {:.0f} ms",
        'stat_score': "Sector Score: {}",
        'stat_combo': "Max Combo: {}",
        'stat_rt_none': "No Response",
        'ach_title': "[ Sector Evaluation Report ]",
        'ach_none': "Metrics stable. Maintain focus.",
        'mem_title': "Core Reconstruction Quality",
        'mem_status': ["Core De-synced", "Link Unstable", "Stable", "Perfect Synchronization!"],
        'cont_hint': "Press any key to continue",
        'end_title': "All Induction Sectors Completed",
        'end_score': "Final Command Score: {}",
        'end_save': "Data uploaded to secure terminal",
        'end_demo': "Simulation session ended",
        'end_exit': "Press any key to disconnect"
    }
}

# ==================== 2. LSL 时间同步模块 ====================
try:
    from pylsl import StreamInfo, StreamOutlet
    LSL_AVAILABLE = True
except ImportError:
    LSL_AVAILABLE = False

class MarkerStream:
    def __init__(self, name="N_Back_Markers", type="Markers"):
        self.active = False
        if LSL_AVAILABLE:
            info = StreamInfo(name, type, 1, 0, 'string', 'nback_uid_67890')
            self.outlet = StreamOutlet(info)
            self.active = True
            print(f"[LSL] Stream '{name}' established.")
        else:
            print("[LSL] pylsl not found. Hardware sync disabled.")

    def push(self, marker_str):
        if self.active: self.outlet.push_sample([marker_str])

# ---------------------- Config & Assets ---------------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "results")

def get_chinese_font_path():
    system = platform.system()
    if system == "Windows": fonts = [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]
    elif system == "Darwin": fonts = [r"/System/Library/Fonts/PingFang.ttc", r"/System/Library/Fonts/STHeiti Light.ttc"]
    else: fonts = [r"/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"]
    for f in fonts:
        if os.path.exists(f): return f
    return None 

CH_FONT_PATH = get_chinese_font_path()
SCREEN_SIZE = (1000, 650)
FPS, ACH_FONT_SIZE = 60, 20
BG_COLOR, TEXT_COLOR, HIGHLIGHT_COLOR = (5, 5, 20), (200, 255, 255), (0, 255, 100)
PANEL_BG, PANEL_BORDER = (10, 20, 40), (0, 120, 200)
INPUT_BG, INPUT_ACTIVE = (30, 40, 60), (50, 70, 100)
TARGET_KEY, NONTARGET_KEY = pygame.K_j, pygame.K_f
LETTERS = ['A', 'C', 'D', 'F', 'H', 'J', 'K', 'L']

DIFFICULTY_SETTINGS = {
    "EASY": {"stim_duration": 1000, "trial_duration": 2500, "trials_per_block": 30, "n_blocks": 4, "target_ratio": 0.33, "n_back": 2},
    "NORMAL": {"stim_duration": 500, "trial_duration": 2000, "trials_per_block": 60, "n_blocks": 6, "target_ratio": 0.30, "n_back": 3},
    "HARD": {"stim_duration": 300, "trial_duration": 1500, "trials_per_block": 80, "n_blocks": 6, "target_ratio": 0.25, "n_back": 3}
}

# ---------------------- Visual Helpers ---------------------- #
def create_base_signal_img():
    size = 260
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    pygame.draw.circle(surf, (0, 150, 255, 60), (cx, cy), 110, 8)
    pygame.draw.circle(surf, (0, 255, 200, 100), (cx, cy), 95, 2)
    pts = [(cx + 60*math.cos(math.pi/3*i+math.pi/6), cy + 60*math.sin(math.pi/3*i+math.pi/6)) for i in range(6)]
    pygame.draw.polygon(surf, (0, 200, 255, 180), pts, 0)
    pygame.draw.polygon(surf, (255, 255, 255, 255), pts, 2)
    pygame.draw.circle(surf, (255, 255, 255, 255), (cx, cy), 15)
    for p in pts: pygame.draw.line(surf, (0, 255, 200, 150), (cx, cy), p, 2)
    return surf

def draw_star_field(screen, stars):
    w, h = screen.get_size()
    for x, y, r in stars:
        pygame.draw.circle(screen, (200, 200, 255) if r >= 2 else (120, 120, 200), (x % w, y % h), r, 0)

def draw_centered_text(screen, lines, font, color=TEXT_COLOR, spacing=15, offset_y=0):
    if isinstance(lines, str): lines = [lines]
    surfs = [font.render(line, True, color) for line in lines]
    total_h = sum(s.get_height() for s in surfs) + spacing * (len(surfs)-1)
    y = (screen.get_height() - total_h) // 2 + offset_y
    for s in surfs:
        screen.blit(s, ((screen.get_width() - s.get_width()) // 2, y))
        y += s.get_height() + spacing

def get_memory_replay_surface(acc, base_img):
    if not base_img: return None
    w, h = base_img.get_size()
    scale = 0.1 if acc < 0.3 else 0.2 if acc < 0.5 else 0.4 if acc < 0.7 else 0.7 if acc < 0.85 else 1.0
    img = pygame.transform.scale(pygame.transform.smoothscale(base_img, (max(1, int(w*scale)), max(1, int(h*scale)))), (w, h))
    if acc < 0.7:
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, int((0.7 - acc) / 0.7 * 180 + 40)))
        img.blit(overlay, (0, 0))
    return img

# ---------------------- Logic Helpers ---------------------- #
def calculate_achievements(acc, best_combo, mean_rt, lang):
    ach = []
    # Simplified achievement set for bilingual support
    if best_combo >= 5: ach.append(("Link Sync", "Combo over 5"))
    if acc >= 0.9: ach.append(("Cyber Brain", "Accuracy over 90%"))
    return ach

class InputBox:
    def __init__(self, x, y, w, h, font, label=""):
        self.rect, self.color, self.text, self.label, self.font, self.active = pygame.Rect(x, y, w, h), INPUT_BG, '', label, font, False
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN: self.active = self.rect.collidepoint(event.pos); self.color = INPUT_ACTIVE if self.active else INPUT_BG
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif len(self.text) < 15 and event.unicode.isprintable(): self.text += event.unicode
    def draw(self, screen):
        screen.blit(self.font.render(self.label, True, (180, 180, 200)), (self.rect.x, self.rect.y - 30))
        pygame.draw.rect(screen, self.color, self.rect, 0); pygame.draw.rect(screen, PANEL_BORDER, self.rect, 2)
        screen.blit(self.font.render(self.text, True, (255, 255, 255)), (self.rect.x + 10, self.rect.y + 10))

# ---------------------- Main App Logic ---------------------- #
def run_block(screen, clock, stars, base_img, font_big, font_small, block_idx, config, L, global_score=0, is_prac=False, marker=None):
    n_trials = 20 if is_prac else config['trials_per_block']
    n_back = config['n_back']
    seq = [random.choice(LETTERS) for _ in range(n_trials)]
    t_indices = random.sample(range(n_back, n_trials), int(n_trials * config['target_ratio']))
    for p in t_indices: seq[p] = seq[p - n_back]
    
    results, b_score, combo, best_combo = [], 0, 0, 0
    mode_text = L['feedback_prac'] if is_prac else L['intro_title'].format(f"{L['hud_sector']} {block_idx}")
    
    screen.fill(BG_COLOR); draw_star_field(screen, stars)
    draw_centered_text(screen, [mode_text, L['rules'].format(n_back), L['start_hint']], font_small)
    pygame.display.flip()
    
    # Wait for key
    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN: waiting = False
            
    if marker: marker.push(f"Block_{block_idx}_Start")

    for i, stim in enumerate(seq):
        t0 = pygame.time.get_ticks()
        resp, rt, r_key, is_t, marked = False, -1, None, (i >= n_back and stim == seq[i-n_back]), False
        while True:
            dt = pygame.time.get_ticks() - t0
            if dt >= config['trial_duration']: break
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN and not resp and e.key in [TARGET_KEY, NONTARGET_KEY]:
                    resp, r_key, rt = True, e.key, dt
                    if marker: marker.push(f"Resp_{pygame.key.name(e.key)}_RT_{rt}")
            
            screen.fill(BG_COLOR); draw_star_field(screen, stars)
            # HUD
            pygame.draw.rect(screen, PANEL_BG, (0, 0, screen.get_width(), 40))
            l_hud = font_small.render(f"{L['hud_core']}: {n_back}-Back | {L['hud_sector']}: {block_idx} | {L['hud_signal']}: {i+1}/{n_trials}", True, (0, 255, 200))
            r_hud = font_small.render(f"{L['hud_energy']}: {b_score} | {L['hud_total']}: {global_score + b_score}", True, (255, 200, 100))
            screen.blit(l_hud, (20, 8)); screen.blit(r_hud, (screen.get_width() - r_hud.get_width() - 20, 8))
            
            if dt < config['stim_duration']:
                if not marked and marker: marker.push(f"Stim_{stim}_{'T' if is_t else 'N'}"); marked = True
                txt = font_big.render(stim, True, TEXT_COLOR); screen.blit(txt, txt.get_rect(center=(screen.get_width()//2, screen.get_height()//2)))
            else:
                cx, cy = screen.get_width()//2, screen.get_height()//2
                pygame.draw.circle(screen, (0, 80, 120), (cx, cy), 100, 1)
                pygame.draw.line(screen, (0, 255, 150), (cx, cy), (cx + 100*math.cos(dt/config['trial_duration']*2*math.pi), cy + 100*math.sin(dt/config['trial_duration']*2*math.pi)), 2)
            pygame.display.flip(); clock.tick(FPS)

        correct = 1 if (is_t and r_key == TARGET_KEY) or (not is_t and r_key == NONTARGET_KEY) else 0
        if correct: b_score += 10; combo += 1; best_combo = max(best_combo, combo)
        else: b_score = max(0, b_score - 5); combo = 0
        results.append({"block": block_idx, "trial": i+1, "correct": correct, "rt": rt, "is_practice": int(is_prac)})

    # Feedback
    acc = sum(r['correct'] for r in results) / len(results)
    mean_rt = statistics.mean([r['rt'] for r in results if r['correct'] and r['rt'] > 0]) if [r['rt'] for r in results if r['correct']] else 0
    screen.fill(BG_COLOR); draw_star_field(screen, stars)
    
    # Draw Boxes
    l_box, r_box = pygame.Rect(40, 80, 440, 490), pygame.Rect(520, 80, 440, 490)
    pygame.draw.rect(screen, PANEL_BG, l_box); pygame.draw.rect(screen, PANEL_BORDER, l_box, 2)
    pygame.draw.rect(screen, PANEL_BG, r_box); pygame.draw.rect(screen, PANEL_BORDER, r_box, 2)
    
    f_title = L['feedback_prac'] if is_prac else L['feedback_title'].format(block_idx, config['n_blocks'])
    lines = [f_title, L['stat_acc'].format(acc*100), L['stat_rt'].format(mean_rt) if mean_rt > 0 else L['stat_rt_none'], L['stat_score'].format(b_score), L['stat_combo'].format(best_combo)]
    y_off = 100
    for ln in lines: screen.blit(font_small.render(ln, True, (200, 240, 255)), (60, y_off)); y_off += 40
    
    # Memory Image
    screen.blit(font_small.render(L['mem_title'], True, (0, 220, 255)), (r_box.centerx - 80, 100))
    core_img = get_memory_replay_surface(acc, base_img)
    if core_img:
        screen.blit(core_img, core_img.get_rect(center=r_box.center))
        m_txt = L['mem_status'][0 if acc < 0.3 else 1 if acc < 0.7 else 2 if acc < 0.9 else 3]
        screen.blit(font_small.render(m_txt, True, (200, 240, 255)), (r_box.centerx - 60, r_box.bottom - 50))

    draw_centered_text(screen, L['cont_hint'], font_small, offset_y=250)
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN: waiting = False
    if marker: marker.push(f"Block_{block_idx}_End")
    return results, b_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", type=str, default='zh', choices=['zh', 'en'])
    args = parser.parse_args()
    L = LANG_CONFIG[args.lang]

    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption(L['title'])
    
    f_path = CH_FONT_PATH if args.lang == 'zh' else None
    font_big = pygame.font.Font(f_path, 120) if f_path else pygame.font.SysFont(None, 120)
    font_small = pygame.font.Font(f_path, 24) if f_path else pygame.font.SysFont(None, 24)

    stars = [(random.randint(0, SCREEN_SIZE[0]), random.randint(0, SCREEN_SIZE[1]), random.randint(1, 3)) for _ in range(90)]
    base_img = create_base_signal_img()
    marker = MarkerStream()
    
    # 1. Login
    sub_id, sess_id, save_data = "Sub01", "01", True
    box_sub, box_sess = InputBox(350, 250, 300, 50, font_small, L['sub_label']), InputBox(350, 350, 300, 50, font_small, L['sess_label'])
    btn = pygame.Rect(420, 480, 160, 50)
    while True:
        screen.fill(BG_COLOR); draw_star_field(screen, stars)
        draw_centered_text(screen, L['login_title'], font_small, color=HIGHLIGHT_COLOR, offset_y=-180)
        box_sub.draw(screen); box_sess.draw(screen)
        pygame.draw.rect(screen, (0, 60, 120), btn); pygame.draw.rect(screen, (0, 150, 255), btn, 2)
        screen.blit(font_small.render(L['enter_btn'], True, (255, 255, 255)), (btn.x+40, btn.y+10))
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(e.pos): sub_id, sess_id = box_sub.text or "Sub01", box_sess.text or "01"; break
            box_sub.handle_event(e); box_sess.handle_event(e)
        else: pygame.display.flip(); continue
        break

    # 2. Difficulty
    config, diff_name = DIFFICULTY_SETTINGS["NORMAL"], "NORMAL"
    rects = [(pygame.Rect(260, 200 + i*100, 480, 80), k) for i, k in enumerate(["EASY", "NORMAL", "HARD"])]
    while True:
        screen.fill(BG_COLOR); draw_star_field(screen, stars)
        draw_centered_text(screen, L['diff_title'], font_small, color=HIGHLIGHT_COLOR, offset_y=-180)
        for r, k in rects:
            pygame.draw.rect(screen, (0, 60, 120) if r.collidepoint(pygame.mouse.get_pos()) else PANEL_BG, r); pygame.draw.rect(screen, PANEL_BORDER, r, 2)
            screen.blit(font_small.render(f"{k} - {L['diff_labels'][k]}", True, (255, 255, 255)), (r.x + 20, r.y + 25))
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                for r, k in rects:
                    if r.collidepoint(e.pos): config, diff_name = DIFFICULTY_SETTINGS[k], k; break
                else: continue
                break
        else: pygame.display.flip(); continue
        break

    # 3. Task
    total_score, all_results = 0, []
    # Practice
    res, sc = run_block(screen, pygame.time.Clock(), stars, base_img, font_big, font_small, 0, config, L, marker=marker, is_prac=True)
    all_results.extend(res)
    # Main Blocks
    for b in range(1, config['n_blocks'] + 1):
        res, sc = run_block(screen, pygame.time.Clock(), stars, base_img, font_big, font_small, b, config, L, global_score=total_score, marker=marker)
        total_score += sc
        # KSS
        screen.fill(BG_COLOR); draw_centered_text(screen, [L['kss_title'].format(b), ""] + L['kss_opts'] + ["", L['kss_hint']], font_small)
        pygame.display.flip()
        k_val = 5
        while True:
            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN and pygame.K_1 <= e.key <= pygame.K_9: k_val = e.key - pygame.K_0; break
            else: continue
            break
        for r in res: r.update({'kss': k_val, 'subject_id': sub_id, 'session': sess_id, 'difficulty': diff_name})
        all_results.extend(res)
        
        # Save CSV
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        csv_path = os.path.join(OUTPUT_DIR, f"{sub_id}_{sess_id}_{diff_name}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['subject_id', 'session', 'difficulty', 'block', 'trial', 'correct', 'rt', 'kss', 'is_practice'])
            writer.writeheader(); writer.writerows([{k: d.get(k, "") for k in writer.fieldnames} for d in all_results])

    # End
    screen.fill(BG_COLOR); draw_centered_text(screen, [L['end_title'], L['end_score'].format(total_score), L['end_save'], L['end_exit']], font_small)
    pygame.display.flip()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN or e.type == pygame.QUIT: pygame.quit(); sys.exit()

if __name__ == "__main__":
    main()