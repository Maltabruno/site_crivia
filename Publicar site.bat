@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo  === Publicar o site da CRIVIA ===
echo.
rem So publica a partir do ramo principal. Copias de previa (outros ramos) nao vao para o ar por engano.
for /f "delims=" %%b in ('git branch --show-current') do set RAMO=%%b
if not "%RAMO%"=="main" (
  echo  Esta pasta e uma copia de previa ^(ramo %RAMO%^). Nada foi publicado.
  echo  Para publicar, use a pasta site_crivia depois da aprovacao.
  echo.
  pause
  exit /b 1
)
echo  1/2 Enviando os arquivos para o GitHub (ramo main)...
git add -A
git commit -m "Atualiza o site"
git push origin main
echo.
echo  2/2 Publicando a pasta site_crivia_padrao (ramo gh-pages)...
git subtree push --prefix site_crivia_padrao origin gh-pages
echo.
echo  Pronto. O site novo aparece em 1 a 2 minutos em https://www.criviaengenharia.com.br
echo.
pause
