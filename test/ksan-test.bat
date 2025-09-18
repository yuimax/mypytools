@echo off

set cmd=..\bin\ksan.py

echo -------------------------
echo ksan.py 1 + 2
%cmd% 1 + 2

echo -------------------------
echo ksan.py 2 ** 16
%cmd%  2 ** 16

echo -------------------------
echo ksan.py math.cos(math.pi)
%cmd%  math.cos(math.pi)
