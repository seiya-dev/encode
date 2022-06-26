@echo off

set isbatch=true

set useNVEnc=y
set audioTrackIndex=0
set encodeAudio=y
set subsTrackIndex=0
set subsFileIndex=0

for %%a in ("*.mkv") do (
    @call "%~dp0.\ffmpeg-nvencc_encode_video.py" "%%a"
)

set useNVEnc=
set audioTrackIndex=
set encodeAudio=
set subsTrackIndex=
set subsFileIndex=

pause
