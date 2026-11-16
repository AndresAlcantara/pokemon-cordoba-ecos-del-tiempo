@echo off
set ts=%date:~-4%-%date:~3,2%-%date:~0,2%_%time:~0,2%%time:~3,2%
set ts=%ts: =0%
copy "%~dp0MiHack.gba" "%~dp0respaldos\MiHack_%ts%.gba"
echo Respaldo creado en la carpeta respaldos.
pause
