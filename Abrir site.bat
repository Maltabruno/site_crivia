@echo off
cd /d "%~dp0"
title CRIVIA - Site CRIVIA padrao (feche esta janela para encerrar)
echo Abrindo o Site CRIVIA padrao...
echo Para encerrar, feche esta janela.
python -I Site_crivia.py
if errorlevel 1 py -I Site_crivia.py
pause
