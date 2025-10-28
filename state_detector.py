import cv2
from utils import match_template, load_template, log, mean_score

# =======================================
# 状态识别模块
# =======================================

class StateDetector:
    def __init__(self, threshold=0.8):
        self.threshold = threshold
        self.templates = {
            "port": load_template("port.png"),
            "queue": load_template("queue.png"),
            "battle_ui": load_template("battle_ui_indicator.png"),
            "victory": load_template("victory.png"),
            "defeat": load_template("defeat.png"),
        }

    def detect_state(self, screen_gray):
        """检测当前游戏状态"""
        scores = {}
        for key, tpl in self.templates.items():
            _, score = match_template(screen_gray, tpl, self.threshold)
            scores[key] = score

        # 记录详细日志
        log(f"[状态检测] 分数={scores}")

        # 状态判断逻辑
        if scores["victory"] > 0.85 or scores["defeat"] > 0.85:
            return "RESULT"
        if scores["battle_ui"] > 0.8:
            return "BATTLE"
        if scores["queue"] > 0.85:
            return "QUEUE"
        if scores["port"] > 0.85:
            return "PORT"
        return "UNKNOWN"
