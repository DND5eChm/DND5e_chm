@echo off
set /p file=你要运行的python文件名（无后缀）：
:1
python %file%.py
echo 点按以重复运行
pause
goto 1