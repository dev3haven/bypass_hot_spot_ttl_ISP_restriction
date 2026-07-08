@echo off
chcp 65001 >nul
cd /d "%~dp0"
pythonw.exe ttl_gui.py
if %errorlevel% neq 0 (
    echo Failed to start with pythonw.exe, trying python.exe...
    python.exe ttl_gui.py
)
