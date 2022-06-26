@echo off

echo.
echo :: MP4 Muxer ::
echo.

set space=false
if "%title%"=="" set space=true
if "%lang%"=="" set space=true

if "%title%"=="" set /p title=Video Title: 
if "%lang%"=="" set /p lang=Audio Lang [3-code]: 

set "outputdir=%~dp1"
set "filename=%~n1"
set "fileext=%~nx1"
set "inext=%~x1"

if exist "%filename%.mp4"       set "audio_file=%filename%.mp4"
if exist "%filename%.audio.mp4" set "audio_file=%filename%.audio.mp4"
if exist "%filename%.m4a.mp4"   set "audio_file=%filename%.m4a.mp4"
if exist "%filename%.flac"      set "audio_file=%filename%.flac"
if exist "%filename%.ac3"       set "audio_file=%filename%.ac3"
if exist "%filename%.m1a"       set "audio_file=%filename%.m1a"
if exist "%filename%.m2a"       set "audio_file=%filename%.m2a"
if exist "%filename%.mp3"       set "audio_file=%filename%.mp3"
if exist "%filename%.m4a"       set "audio_file=%filename%.m4a"
if exist "%filename%.128kb.m4a" set "audio_file=%filename%.128kb.m4a"
if exist "%filename%.192kb.m4a" set "audio_file=%filename%.192kb.m4a"
if exist "%filename%.aac"       set "audio_file=%filename%.aac"
if exist "%filename%_track1-fix.aac" set "audio_file=%filename%_track1-fix.aac"
if exist "%filename%_track1.aac" set "audio_file=%filename%_track1.aac"

if exist "%filename%.srt"       set "srt_file=%filename%.srt"

if not "%srt_file%"=="" (
    if "%slang%"=="" set /p slang=Subs Lang [3-code]: 
    if "%slang%"=="" set space=true
)

if "%space%"=="true" (
    echo.
)

set "outfilename=%filename%"
if exist "%outfilename%.mp4" set "outfilename=%outfilename%_muxed"

echo ... Muxing to "%outfilename%.mp4" ...
echo.

set "vid_cmd="
set "aud_cmd="
set "srt_cmd="
set "aud_out=.mp4"
if not "%inext%"==".aac" ( set vid_cmd=-add "%fileext%#video:name=%title%" )
if not "%inext%"==".aac" echo %fileext%#video:name=%title%
if not "%audio_file%"=="" ( set aud_cmd=-add "%audio_file%#audio:name=:lang=%lang%" )
if not "%audio_file%"=="" echo %audio_file%#audio:name=:lang=%lang%
if not "%srt_file%"=="" ( set srt_cmd=-add "%srt_file%#:name=:lang=%slang%" )
if not "%srt_file%"=="" echo %srt_file%#:name=:lang=%slang%
if "%inext%"==".aac" ( set "aud_out=.m4a" )
rem :fps=23.976

echo.
"mp4box" -for-test ^
    -tmp "%TEMP%" ^
    -brand mp42:1 -ab mp41 ^
    -ab iso6 -ab isom -rb iso2 ^
    %vid_cmd% ^
    %aud_cmd% ^
    %srt_cmd% ^
    -new "%outputdir%%outfilename%%aud_out%"
echo.

if "%isbatch%"=="" (
    pause
)
