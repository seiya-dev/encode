vFolder = "D:\Videos\Anime\[RelGroup] Title (BD 1080p x265 10-bit FLAC) [BATCH]\"
vEpName = "[RelGroup] Title - 01 (BD 1080p x265 10-bit FLAC) [00000000].mkv"

global glob_cache_dir  = vFolder
global glob_source_dir = vFolder

bs(vEpName + ".mkv", atrack=1)
v = last

vtrim0 = v.trim(0, -1000000).spresize36(854, 480)
vtrim1 = v.trim(0, -1000000).spresize36(854, 480).KillAudio()

return vtrim0
