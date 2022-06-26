@echo off

set isbatch=true

for %%a in ("*.mp4", "*.m4a") do (
    @call "%~dp0.\mp4box_demux_all_tracks.bat" "%%a"
)

pause
