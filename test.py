import win32gui
import win32con
import win32api
import ctypes

def get_window_rect(title: str):
    hwnd = win32gui.FindWindow(None, title)
    if not hwnd:
        raise RuntimeError(f"未找到窗口: {title}")

    # 获取窗口矩形（包含边框、标题栏）
    rect = win32gui.GetWindowRect(hwnd)
    l, t, r, b = rect
    w = r - l
    h = b - t

    # 获取客户区矩形（不包含边框）
    client_rect = win32gui.GetClientRect(hwnd)
    cl, ct, cr, cb = client_rect
    client_w = cr - cl
    client_h = cb - ct

    # 将客户区左上角转换为屏幕坐标
    client_point = win32gui.ClientToScreen(hwnd, (0, 0))
    cx, cy = client_point

    rect_info = {
        "hwnd": hwnd,
        "left": cx,
        "top": cy,
        "right": cx + client_w,
        "bottom": cy + client_h,
        "width": client_w,
        "height": client_h,
    }

    print(f"[INFO] 窗口 '{title}' 客户区坐标: ({cx},{cy}) 大小 {client_w}x{client_h}")
    return rect_info


if __name__ == "__main__":
    win = get_window_rect("《战舰世界》")
    print(win)
    input("\n按回车键退出...")
