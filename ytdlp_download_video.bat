@echo off

set yturl=%~1
if "%~1" == "" set /p yturl=Video URL: 
set crdr=%cd%
set outdir=D:\Videos
set output=%outdir%\%%(title)s-%%(id)s-%%(height)s-f%%(format_id)s.%%(ext)s

yt-dlp -F "%yturl%"
echo BEST: bestvideo[ext=mp4],bestaudio[ext=m4a]/best[ext=mp4]/best
set /p formatlist=VideoQuality: 
yt-dlp -k --all-subs -f "%formatlist%" "%yturl%" -o "%output%"

cd /d %outdir%
for %%a in ("*.vtt") do (
    SubtitleEdit /convert "%%a" subrip
)

cd /d %crdr%
pause
