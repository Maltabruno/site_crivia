@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  === Gerar cartoes e paginas de Experiencia e Resultados ===
echo.
python -I scripts\gerar_experiencias.py
echo.
echo  Pronto. Isto so atualiza os arquivos nesta pasta. Nada foi publicado.
echo.
pause
