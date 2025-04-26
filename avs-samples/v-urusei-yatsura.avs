global glob_cache_dir  = "./cache/"
global glob_source_dir = "./v_temp/"

vFolder = "GD:\Shared\Anime U\Urusei Yatsura\"
vFolder = vFolder + "Urusei Yatsura OVAs 01-12 (1985-2008)\"
vEpName  = "Urusei Yatsura OVA - Nagisa's Fiance (1988)"

v = bs(vEpName + ".mkv", source_dir = vFolder)
v = v.ASSSource(vEpName + "_track3.ass", source_dir = vFolder)

vtrim = []
vtrim = ArrayAdd(vtrim, v.trim(1, -1000000).z_Spline36Resize(854, 480))
vtrim = ArrayAdd(vtrim, v.trim(31322, 31591) + v.trim(31655, 32197) + v.trim(32234, 32398))

vtrim[0]
