import cv2
import numpy as np
import pyautogui
import time
import win32gui
import win32con
import win32api
import threading
import keyboard
import os

# ---------------- 全局配置 ----------------
GAME_TITLE = "《战舰世界》"
BASE_RES = (1920, 1080)
STATE = "IDLE"
RUNNING = False
last_action_time = 0
auto_nav_checked = False

# ---------------- 工具函数 ----------------

def log(msg):
    print(time.strftime("[%H:%M:%S] "), msg)

def press_key_hex(hex_key_code):
    """底层硬件键盘事件（DirectX兼容）"""
    win32api.keybd_event(hex_key_code, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(hex_key_code, 0, win32con.KEYEVENTF_KEYUP, 0)

def open_map():
    log("[ACTION] 打开地图 (M)")
    press_key_hex(0x4D)  # 'M'
    time.sleep(0.5)

def close_map():
    log("[ACTION] 关闭地图 (M)")
    press_key_hex(0x4D)
    time.sleep(0.5)

def get_window_rect(title):
    hwnd = win32gui.FindWindow(None, title)
    if hwnd == 0:
        log(f"[ERROR] 未找到窗口: {title}")
        return None
    rect = win32gui.GetClientRect(hwnd)
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    width, height = rect[2] - rect[0], rect[3] - rect[1]
    log(f"[INFO] 窗口 '{title}' 客户区坐标: ({left},{top}) 大小 {width}x{height}")
    return {'hwnd': hwnd, 'left': left, 'top': top, 'width': width, 'height': height}

def get_window_screenshot(window):
    """截取窗口画面"""
    x, y, w, h = window['left'], window['top'], window['width'], window['height']
    img = pyautogui.screenshot(region=(x, y, w, h))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def find_template(screen, template_path, threshold=0.6, base_res=(1920,1080), window_res=None):
    """自动适配缩放的模板匹配"""
    if not os.path.exists(template_path):
        log(f"[WARN] 模板不存在: {template_path}")
        return None, 0.0

    template = cv2.imread(template_path)
    if template is None or screen is None:
        return None, 0.0

    if window_res is not None:
        scale_x = window_res[0] / base_res[0]
        scale_y = window_res[1] / base_res[1]
        template = cv2.resize(template, (int(template.shape[1]*scale_x), int(template.shape[0]*scale_y)))

    img_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    tpl_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(img_gray, tpl_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if max_val >= threshold:
        h, w = template.shape[:2]
        center = (max_loc[0] + w // 2, max_loc[1] + h // 2)
        log(f"[MATCH] {os.path.basename(template_path)} match={max_val:.3f} at {center}")
        return center, max_val
    else:
        log(f"[DEBUG] tpl no match {os.path.basename(template_path)} thr={threshold:.2f} max={max_val:.3f}")
        return None, max_val

def click_in_window(window, pos):
    """点击游戏窗口内部坐标"""
    gx = window['left'] + pos[0]
    gy = window['top'] + pos[1]
    pyautogui.moveTo(gx, gy, duration=0.15)
    pyautogui.click()
    log(f"[CLICK] 点击游戏坐标 {pos} (全屏 {gx},{gy})")

# ---------------- 状态机 ----------------

def main_loop():
    global STATE, RUNNING, last_action_time, auto_nav_checked

    window = get_window_rect(GAME_TITLE)
    if not window:
        log("[FATAL] 未找到游戏窗口，退出。")
        return

    while RUNNING:
        try:
            screen = get_window_screenshot(window)
            res = (window['width'], window['height'])

            if STATE == "IDLE":
                pos, conf = find_template(screen, "templates/start_battle.png", 0.6, BASE_RES, res)
                if pos:
                    click_in_window(window, pos)
                    STATE = "LOADING"
                    last_action_time = time.time()
                    continue

            elif STATE == "LOADING":
                pos, conf = find_template(screen, "templates/battle_ui_indicator.png", 0.6, BASE_RES, res)
                if pos:
                    log("[STATE] 检测到战斗UI -> 转入 MAP_NAV")
                    STATE = "MAP_NAV"
                    continue

                if time.time() - last_action_time > 60:
                    log("[TIMEOUT] 匹配超时，重试返回大厅")
                    STATE = "IDLE"

            elif STATE == "MAP_NAV":
                open_map()
                found = False
                for tpl in ["cap_point_A.png", "cap_point_B.png", "cap_point_C.png"]:
                    path = os.path.join("templates", tpl)
                    pos, conf = find_template(screen, path, 0.6, BASE_RES, res)
                    if pos:
                        click_in_window(window, pos)
                        found = True
                        time.sleep(0.3)
                close_map()
                auto_nav_checked = True
                STATE = "COMBAT"
                continue

            elif STATE == "COMBAT":
                # 检查是否失去自动导航
                if not auto_nav_checked:
                    log("[CHECK] 检测到无自动导航 -> 再次进入 MAP_NAV")
                    STATE = "MAP_NAV"
                    continue

                # 检测胜利/失败
                for tpl in ["victory.png", "defeat.png"]:
                    path = os.path.join("templates", tpl)
                    pos, conf = find_template(screen, path, 0.7, BASE_RES, res)
                    if pos:
                        log("[STATE] 战斗结束 -> 返回大厅")
                        STATE = "RESPAWN"
                        break

            elif STATE == "RESPAWN":
                pos, conf = find_template(screen, "templates/back_to_lobby.png", 0.6, BASE_RES, res)
                if pos:
                    click_in_window(window, pos)
                    STATE = "IDLE"
                    continue

            time.sleep(0.5)

        except Exception as e:
            log(f"[ERROR] {e}")
            time.sleep(1)

    log("[STOP] 已安全停止主循环。")

# ---------------- 控制逻辑 ----------------

def toggle_run():
    global RUNNING
    RUNNING = not RUNNING
    if RUNNING:
        log("[F8] 启动自动脚本")
        threading.Thread(target=main_loop, daemon=True).start()
    else:
        log("[F8] 停止自动脚本")

keyboard.add_hotkey("F8", toggle_run)
log("按 F8 启动/停止脚本。按 Ctrl+C 退出。")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    RUNNING = False
    log("用户退出。")
