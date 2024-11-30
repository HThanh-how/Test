@echo off
:: Thêm vào startup registry
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "AutoGitCommit" /t REG_SZ /d "\"%~dp0auto_commit.py\"" /f

:: Chạy script
start /min "" "C:\Users\Admin\AppData\Local\Programs\Python\Python312\pythonw.exe" auto_commit.py 