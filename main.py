import time
import keyboard
import pyautogui
import cv2
import numpy as np
from utils import log, to_gray
from state_detector import StateDetector
import config

# ============================================
# 主程序：自动状态机控制脚本
# ============================================

running = False
detector = StateDetector(threshold=config.TEMPLATE_MATCH_THRESHOLD)
last_state = None

def screenshot():
    """截取当前屏幕"""
    img = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return img

def click(x, y, desc="点击"):
    """点击动作"""
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.click()
    log(f"[操作] {desc} 于坐标 ({x}, {y})")

def main_loop():
    """主循环"""
    global running, last_state

    log("[系统] 启动脚本，按 F8 暂停/恢复，F9 退出")

    while True:
        if keyboard.is_pressed(config.HOTKEY_EXIT):
            log("[系统] 收到退出指令，程序终止")
            break

        if keyboard.is_pressed(config.HOTKEY_START):
            running = not running
            log(f"[系统] 运行状态切换为：{'运行中' if running else '暂停'}")
            time.sleep(0.5)

        if not running:
            time.sleep(0.5)
            continue

        # 截图并分析
        screen = screenshot()
        gray = to_gray(screen)
        state = detector.detect_state(gray)

        if state != last_state:
            log(f"[状态变化] {last_state} → {state}")
            last_state = state

        # 状态对应操作
        if state == "PORT":
            log("[行为] 检测到港口，准备点击“加入战斗”按钮")
            click(960, 850, "加入战斗")
        elif state == "QUEUE":
            log("[行为] 匹配中，等待进入战斗")
            time.sleep(3)
        elif state == "BATTLE":
            log("[行为] 战斗中，检测是否需要自动导航或其他操作")
            time.sleep(5)
        elif state == "RESULT":
            log("[行为] 战斗结果界面，点击返回港口")
            click(960, 900, "返回港口")
            time.sleep(3)
        else:
            log("[提示] 当前状态未识别，等待下一次检测")

        time.sleep(config.STATE_CHECK_INTERVAL)

if __name__ == "__main__":
    log("============== 战舰世界自动脚本 启动 ==============")
    main_loop()
