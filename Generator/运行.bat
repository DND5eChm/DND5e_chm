@echo off
if "%1" NEQ "" goto open_loop
set /p file=��Ҫ���е�python�ļ������޺�׺����
echo ��ʼ����
:loop
python %file%.py
echo �㰴��������ظ����У�%file%
pause
goto loop
:open_loop
python %1
echo �㰴��������ظ����У�%~n1
pause
goto open_loop