@echo off
if "%1" NEQ "" goto open_loop
set /p file=你要运行的python文件名（无后缀）：
echo 开始运行
:loop
python %file%.py
echo 点按任意键以重复运行：%file%
pause
goto loop
:open_loop
python %1
echo 点按任意键以重复运行：%~n1
pause
goto open_loop