# GetSystemEnv.dll
# BestSource.dll
# assrender.dll

# resize4psp.avs

pspOutput = GetSystemEnv("_avsOutput")
sizes = [[640,480], [720,480], [720,576]]

cachepath = GetSystemEnv("_cachePath")
inputfile = GetSystemEnv("_inputFile")

if(IsString(pspOutput) && pspOutput == "video"){
    pspEncMode  = Int(Value(GetSystemEnv("_pspEncMode")))
    pspAnamorph = GetSystemEnv("_pspAnamorph")
    
    subsfile   = GetSystemEnv("_subsFile")
    fontsdir   = GetSystemEnv("_fontsDir")
    
    video = BSVideoSource(inputfile, cachemode = 4, cachepath = cachepath)
    
    if(IsString(subsfile) && subsfile != ""){
        video = video.assrender(subsfile, fontdir = fontsdir, debuglevel = 5)
    }
    if(pspAnamorph != "0"){
        video = video.Spline36Resize(sizes[pspAnamorph][0], sizes[pspAnamorph][1])
    }
    else{
        video = video.resize4psp(pspEncMode)
    }
    return video
}

if(IsString(pspOutput) && pspOutput == "audio"){
    audiotrack = GetSystemEnv("_aTrack")
    
    audio = BSAudioSource(inputfile, track = Value(audiotrack), cachemode = 4, cachepath = cachedir)
    return audio
}
