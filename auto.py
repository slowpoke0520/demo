import cv2
import numpy as np
import pyautogui
import time
import keyboard
import win32gui
import win32con
import os

# ==============================
# 配置
# ==============================
GAME_TITLE = "《战舰世界》"
TEMPLATE_DIR = "templates"
DEBUG = True

STATE_IDLE = "idle"
STATE_LOADING = "loading"
STATE_COMBAT = "combat"
STATE_END = "end"

running = False
window_rect = None
current_state = STATE_IDLE


# ==============================
# 基础函数
# ==============================
def dbg(msg):
    if DEBUG:
        print(f"[INFO] {time.strftime('%H:%M:%S')} {msg}")

def get_window_rect(title):
    hwnd = win32gui.FindWindow(None, title)
    if hwnd == 0:
        raise Exception(f"未找到窗口: {title}")
    rect = win32gui.GetClientRect(hwnd)
    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.ClientToScreen(hwnd, (rect[2], rect[3]))
    return {
        "hwnd": hwnd,
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "width": right - left,
        "height": bottom - top
    }

def capture_window():
    global window_rect
    if not window_rect:
        return None
    img = pyautogui.screenshot(region=(window_rect["left"], window_rect["top"], window_rect["width"], window_rect["height"]))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def find_template(screen, window_rect, template_path, threshold=0.8):
    if not os.path.exists(template_path):
        return None
    tpl = cv2.imread(template_path)
    res = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val >= threshold:
        x, y = max_loc
        cx = window_rect["left"] + x + tpl.shape[1] // 2
        cy = window_rect["top"] + y + tpl.shape[0] // 2
        return (cx, cy)
    return None

def game_click(pos):
    pyautogui.moveTo(pos[0], pos[1])
    pyautogui.click()
    dbg(f"[CLICK] 点击位置 {pos}")

# ==============================
# 动作确认机制
# ==============================
def click_with_confirm(click_templates, confirm_templates, max_retry=3, delay_between=2.0, threshold=0.8):
    """
    点击按钮后确认是否切换成功。
    click_templates: [list] 可能的按钮图片路径
    confirm_templates: [list] 进入后应检测到的图标路径
    """
    for attempt in range(max_retry):
        screen = capture_window()
        if screen is None:
            dbg("[ERROR] 无法截取游戏画面")
            return False

        # 查找可能的点击按钮
        click_pos = None
        for tpl in click_templates:
            pos = find_template(screen, window_rect, os.path.join(TEMPLATE_DIR, tpl), threshold)
            if pos:
                click_pos = pos
                dbg(f"[MATCH] 发现按钮 {tpl}，准备点击")
                break

        if click_pos:
            game_click(click_pos)
            dbg("[ACTION] 点击后等待确认中...")
            time.sleep(delay_between)

            # 检查确认标志
            screen = capture_window()
            for confirm_tpl in confirm_templates:
                confirm_pos = find_template(screen, window_rect, os.path.join(TEMPLATE_DIR, confirm_tpl), threshold)
                if confirm_pos:
                    dbg(f"[CONFIRM] 成功检测到 {confirm_tpl} ✅")
                    return True
            dbg(f"[WARN] 未检测到确认标志，准备重试 ({attempt+1}/{max_retry})")
        else:
            dbg(f"[WARN] 未找到任何匹配按钮，重试 ({attempt+1}/{max_retry})")

        time.sleep(delay_between)
    dbg("[FAIL] 点击确认失败 ❌")
    return False


# ==============================
# 主流程逻辑
# ==============================
def main_loop():
    global current_state

    dbg("程序启动，等待检测状态...")
    while running:
        screen = capture_window()
        if screen is None:
            dbg("无法截取游戏窗口，请确认窗口存在")
            time.sleep(2)
            continue

        if current_state == STATE_IDLE:
            dbg("[STATE] 港口状态，尝试点击加入战斗按钮")
            success = click_with_confirm(
                ["start_battle.png", "start_battle_alt.png"],
                ["battle_ui_indicator.png"],
                max_retry=3,
                delay_between=2.5
            )
            if success:
                dbg("[STATE] 成功进入加载阶段")
                current_state = STATE_LOADING
            else:
                dbg("[STATE] 点击失败，保持港口状态")
                time.sleep(3)

        elif current_state == STATE_LOADING:
            dbg("[STATE] 加载中，检测战斗界面是否出现...")
            if find_template(screen, window_rect, os.path.join(TEMPLATE_DIR, "auto_pilot_on.png"), 0.8):
                dbg("[STATE] 检测到战斗UI，进入战斗状态")
                current_state = STATE_COMBAT
            else:
                time.sleep(2)

        elif current_state == STATE_COMBAT:
            dbg("[STATE] 战斗中，检测胜利或失败...")
            if find_template(screen, window_rect, os.path.join(TEMPLATE_DIR, "victory.png"), 0.8) or \
               find_template(screen, window_rect, os.path.join(TEMPLATE_DIR, "defeat.png"), 0.8):
                dbg("[STATE] 检测到结算界面，进入END阶段")
                current_state = STATE_END
            else:
                time.sleep(3)

        elif current_state == STATE_END:
            dbg("[STATE] 结算阶段，检测返回港口按钮")
            if click_with_confirm(
                ["return_port.png"],
                ["start_battle.png", "start_battle_alt.png"],
                max_retry=3,
                delay_between=2.5
            ):
                dbg("[STATE] 返回港口成功，恢复IDLE状态")
                current_state = STATE_IDLE
            else:
                dbg("[STATE] 未能返回港口，重试中")
                time.sleep(3)


# ==============================
# 启动入口
# ==============================
if __name__ == "__main__":
    dbg("按 F8 启动 / 停止脚本")
    while True:
        if keyboard.is_pressed("f8"):
            time.sleep(0.3)
            if not running:
                try:
                    window_rect = get_window_rect(GAME_TITLE)
                    dbg(f"锁定窗口 {GAME_TITLE}: {window_rect}")
                    running = True
                    main_loop()
                except Exception as e:
                    dbg(f"[ERROR] {e}")
                    running = False
            else:
                dbg("脚本已停止")
                running = False
        time.sleep(0.1)
