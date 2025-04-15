# GetSystemEnv.dll
# BestSource.dll

# resize4psp.avs

cachedir   = GetSystemEnv("_cacheDir")
videofile  = GetSystemEnv("_inFile")
outputFile = GetSystemEnv("_outFile")

BSVideoSource(videofile, cachemode = 4, cachepath = cachedir).thumb4psp()
ImageWriter(outputFile, 0, 0, "jpg")
