import os
import cv2
import numpy as np
from datetime import datetime

# ========== 基础路径 ==========
ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(ROOT, "templates")
LOG_DIR = os.path.join(ROOT, "logs")

os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ========== 时间与日志 ==========
def timestamp():
    """返回当前时间字符串"""
    return datetime.now().strftime("%H:%M:%S")

def log(msg):
    """输出并写入日志文件"""
    text = f"[{timestamp()}] {msg}"
    print(text)
    logfile = os.path.join(LOG_DIR, f"log_{datetime.now().date()}.txt")
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def dbg(msg):
    """调试信息"""
    log(f"[调试] {msg}")

# ========== 模板处理 ==========
def ensure_templates_exist():
    """确认模板文件夹存在"""
    if not os.path.exists(TEMPLATE_DIR):
        os.makedirs(TEMPLATE_DIR)
        log(f"[系统] 已创建模板目录 {TEMPLATE_DIR}")
    else:
        log(f"[系统] 模板目录已存在：{TEMPLATE_DIR}")

def load_template(name):
    """加载模板图像"""
    path = os.path.join(TEMPLATE_DIR, name)
    if not os.path.exists(path):
        log(f"[警告] 模板文件 {name} 不存在，请检查 templates 文件夹")
        return None
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        log(f"[错误] 无法读取模板图像 {name}")
    return img

# ========== 图像匹配 ==========
def match_template(screen, template, threshold=0.8):
    """模板匹配，返回坐标与匹配度"""
    if screen is None or template is None:
        return None, 0.0

    res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    h, w = template.shape[:2]

    if max_val >= threshold:
        return (max_loc[0] + w // 2, max_loc[1] + h // 2), max_val
    return None, max_val

# ========== 辅助函数 ==========
def to_gray(img):
    """转灰度"""
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

def crop(image, x, y, w, h):
    """裁剪区域"""
    return image[y:y+h, x:x+w]

def mean_score(values):
    """平均值"""
    return sum(values) / len(values) if values else 0.0
