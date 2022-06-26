@echo off

set useNVEnc=n
set audioTrackIndex=-1
set subsTrackIndex=-1
set subsFileIndex=-1
set toGifv=1

@call "%~dp0.\ffmpeg-nvencc_encode_video.py" "%~1"

set useNVEnc=
set audioTrackIndex=
set subsTrackIndex=
set subsFileIndex=
set toGifv=

pause
