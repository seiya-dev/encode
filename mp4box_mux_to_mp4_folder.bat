@echo off

set /p title=Video Title: 
set /p lang=Audio Lang [3-code]: 
set /p slang=Subs Lang [3-code]: 
set /p onlya=Only Audio (y/N): 

set isbatch=true
if /I "%onlya%" EQU "Y" goto :audio

:both
for %%a in ("*.264","*.h264","*.avc","*.mp4") do (
    @call "%~dp0.\mp4box_mux_to_mp4.bat" "%%a"
)
goto :end

:audio
for %%a in ("*.aac") do (
    @call "%~dp0.\mp4box_mux_to_mp4.bat" "%%a"
)
goto :end

:end
pause
