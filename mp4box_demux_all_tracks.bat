@echo off

set "fileext=%~nx1"

echo :: Demuxing %fileext%
"mp4box" -for-test "%fileext%" -raw * -srt *

if "%isbatch%"=="" (
    pause
)
