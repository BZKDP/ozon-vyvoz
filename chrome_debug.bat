@echo off
REM Запускает ОТДЕЛЬНОЕ окно Chrome с портом отладки 9222 на выделенном профиле.
REM Основной Chrome не трогается (другой user-data-dir = независимый инстанс).
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
 --remote-debugging-port=9222 ^
 --remote-debugging-address=127.0.0.1 ^
 --user-data-dir=".\chrome-debug-profile" ^
 --no-first-run ^
 --no-default-browser-check ^
 "https://seller.ozon.ru/app/fbo-operations/create-supply-return"
