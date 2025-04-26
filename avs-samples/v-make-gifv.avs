global glob_cache_dir  = "./cache/"
global glob_source_dir = "./v_temp/"

vFolder = "D:\Videos\Anime\[RelGroup] Title (BD 1080p x265 10-bit FLAC) [BATCH]\"
vEpName = "[RelGroup] Title - 01 (BD 1080p x265 10-bit FLAC) [00000000].mkv"

v = bs(vEpName, source_dir = vFolder)

vtrim = []
vtrim = ArrayAdd(vtrim, v.trim(1, -1000000).z_Spline36Resize(854, 480))
vtrim = ArrayAdd(vtrim, v.trim(1, 1).z_Spline36Resize(854, 480))

vtrim[0]
