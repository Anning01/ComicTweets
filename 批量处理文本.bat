@echo off
setlocal enabledelayedexpansion

set "errorCount=0"
set "maxErrorCount=9"

:run_script
call .venv\Scripts\activate
python mass_production.py
set "exitCode=%errorlevel%"

if !exitCode! neq 0 (
    set /a "errorCount+=1"
    echo Script failed with exit code !exitCode! on attempt !errorCount!/!maxErrorCount!
    if !errorCount! lss !maxErrorCount! (
        echo Retrying...
        goto :run_script
    ) else (
        echo Maximum error count reached. Exiting...
    )
) else (
    echo Script executed successfully.
)

pause
endlocal