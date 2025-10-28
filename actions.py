import os, time, pyautogui, win32gui, win32con
from utils import match_template, capture_window, dbg, TEMPLATE_DIR

def click_at_screen(x,y,hold=0.08):
    pyautogui.moveTo(x,y,duration=0.08)
    pyautogui.mouseDown()
    time.sleep(hold)
    pyautogui.mouseUp()
    dbg(f"Clicked screen ({x},{y})")

def click_with_confirm(click_templates, confirm_templates, max_retry=3, delay_between=1.5):
    wnd = win32gui.FindWindow(None, "《战舰世界》")
    rect = None
    if wnd:
        cl, ct, cr, cb = win32gui.GetClientRect(wnd)
        left, top = win32gui.ClientToScreen(wnd, (0,0))
        rect = {"left":left,"top":top,"width":cl[2],"height":cl[3]}
    for attempt in range(max_retry):
        img = capture_window()
        # find click template in img
        pos = None
        for tpl in click_templates:
            p,v = match_template(img, os.path.join(TEMPLATE_DIR, tpl), threshold=0.6)
            if p:
                pos = p; break
        if not pos:
            dbg("Click template not found; retrying")
            time.sleep(delay_between)
            continue
        # convert to absolute screen
        x = rect["left"] + pos[0]
        y = rect["top"] + pos[1]
        click_at_screen(x,y)
        time.sleep(delay_between)
        # verify confirm
        img2 = capture_window()
        ok = False
        for ctpl in confirm_templates:
            p2,v2 = match_template(img2, os.path.join(TEMPLATE_DIR, ctpl), threshold=0.5)
            if p2:
                ok=True; break
        if ok:
            dbg("Action confirmed")
            return True
        dbg("Action not confirmed; retry")
    dbg("Action failed after retries")
    return False

def move_window_to_top_left(hwnd):
    try:
        win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0, win32con.SWP_NOSIZE|win32con.SWP_NOZORDER)
    except Exception as e:
        dbg(f"move window error: {e}")