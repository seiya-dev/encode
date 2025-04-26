vFolder = "D:\Videos\Anime\[RelGroup] Title (BD 1080p x265 10-bit FLAC) [BATCH]\"
vEpName = "[RelGroup] Title - 01 (BD 1080p x265 10-bit FLAC) [00000000].mkv"

global glob_cache_dir  = vFolder
global glob_source_dir = vFolder

bs(vEpName + ".mkv", atrack=1)
ConvertBits(16)
v = last

vtrim = []
vtrim = ArrayAdd(vtrim, v.trim(1, -1000000).z_Spline36Resize(854, 480, dither="error_diffusion"))
vtrim = ArrayAdd(vtrim, v.trim(1, 1).z_Spline36Resize(854, 480, dither="error_diffusion").KillAudio())

vtrim[0]
ConvertBits(8)
