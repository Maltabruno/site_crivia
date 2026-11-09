@echo off
cd /d "%~dp0"
title CRIVIA - servidor do site (feche esta janela para encerrar)
echo Gerando e abrindo o site da CRIVIA...
echo Para encerrar, feche esta janela.
python -I Site_crivia.py
if errorlevel 1 py -I Site_crivia.py
pause
