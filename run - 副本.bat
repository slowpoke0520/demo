@echo off
:: 检查是否以管理员身份运行，若不是则自动请求权限
fltmc >nul 2>&1 || (echo 正在请求管理员权限... & cmd /c "powershell -Command Start-Process '%0' -Verb RunAs" && exit /b)

:: 切换到脚本所在目录（H:\Desktop\bot）
cd /d H:\Desktop\demo

:: 运行Python脚本（使用你的Python解释器路径，替换下面的路径）
"C:\Users\raoyi\AppData\Local\Programs\Python\Python310\python.exe" test.py

:: 运行结束后暂停，方便查看结果
pause