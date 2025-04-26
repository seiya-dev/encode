function setGlobPath(string glob_path_name, string "default_path"){
    default_path = Default(default_path, "")
    try {
        if(VarExist(glob_path_name)){
            if(glob_path_name == "glob_source_dir"){
                return IsString(glob_source_dir) ? glob_source_dir : default_path
            }
            if(glob_path_name == "glob_subs_dir"){
                return IsString(glob_subs_dir) ? glob_subs_dir : default_path
            }
            if(glob_path_name == "glob_fonts_dir"){
                return IsString(glob_fonts_dir) ? glob_fonts_dir : default_path
            }
            if(glob_path_name == "glob_cache_dir"){
                return IsString(glob_cache_dir) ? glob_cache_dir : default_path
            }
            return default_path
        }
        return default_path
    }
    catch(e){
        return default_path
    }
}

function bs(string media_file, string "source_dir", string "cache_dir", int "atrack", int_array "framerate", string "vformat"){
    source_dir = Defined(source_dir) ? source_dir : setGlobPath("glob_source_dir")
    cache_dir = Defined(cache_dir) ? cache_dir : setGlobPath("glob_cache_dir")
    cachepath = cache_dir + media_file
    
    atrack = Default(atrack, -1)
    framerate = Default(framerate, [0, 1])
    
    v = BSSource(
        \ source_dir + media_file,
        \ atrack = atrack,
        \ fpsnum = framerate[0],
        \ fpsden = framerate[1],
        \ cachemode = 4,
        \ cachepath = cachepath
        \ )
    
    return v
}

function ASSSource(clip video, string source_file, string "source_dir", string "fonts_dir"){
    source_dir = Defined(source_dir) ? source_dir : setGlobPath("glob_subs_dir")
    fonts_dir = Defined(fonts_dir) ? fonts_dir : setGlobPath("glob_fonts_dir", "./fonts/")
    
    video = video.AssRender(
        \ source_dir + source_file,
        \ fontdir = fonts_dir,
        \ debuglevel = 5
        \ )
    
    return video
}

function lw(string media_file, string "source_dir", string "cache_dir", bool "cache", int "atrack", int_array "framerate", string "vformat"){
    source_dir = Defined(source_dir) ? source_dir : setGlobPath("glob_source_dir")
    cache_dir = Defined(cache_dir) ? cache_dir : setGlobPath("glob_cache_dir")
    cachefile = cache_dir + media_file + ".lwi"
    cache = Default(cache, true)
    
    atrack = Default(atrack, -1)
    framerate = Default(framerate, [0, 1])
    
    vformat = Default(vformat, "YUV420P8")
    
    video = LWLibavVideoSource(
        \ source_dir + media_file,
        \ cachefile = cachefile,
        \ cache = cache,
        \ fpsnum = framerate[0],
        \ fpsden = framerate[1],
        \ format = vformat,
        \ prefer_hw = 1
        \ )
    
    if(atrack > -2){
        audio = LWLibavAudioSource(
            \ source_dir + media_file,
            \ cachefile = cachefile,
            \ stream_index = atrack,
            \ cache = cache
            \ )
        video = AudioDub(video, audio)
    }
    
    return video
}

function lwa(string audio_file, string "source_dir", string "cache_dir", bool "cache", int "atrack"){
    source_dir = Defined(source_dir) ? source_dir : setGlobPath("glob_source_dir")
    cache_dir = Defined(cache_dir) ? cache_dir : setGlobPath("glob_cache_dir")
    cachefile = cache_dir + audio_file + ".lwi"
    cache = Default(cache, true)
    
    atrack = Default(atrack, -1)
    
    audio = LWLibavAudioSource(
        \ source_dir + audio_file,
        \ cachefile = cachefile,
        \ stream_index = atrack,
        \ cache=cache
        \ )
    
    return audio
}

function ff(string media_file, string "source_dir", string "cache_dir", bool "cache", int "atrack", int_array "framerate"){
    source_dir = Defined(source_dir) ? source_dir : setGlobPath("glob_source_dir")
    cache_dir = Defined(cache_dir) ? cache_dir : setGlobPath("glob_cache_dir")
    cachefile = cache_dir + media_file + ".ffindex"
    cache = Default(cache, true)
    
    atrack = Default(atrack, -1)
    framerate = Default(framerate, [-1, 1])
    
    v = FFMS2(
        \ source_dir + media_file,
        \ atrack = atrack,
        \ cachefile = cachefile,
        \ cache = cache,
        \ fpsnum = framerate[0],
        \ fpsden = framerate[1]
        \ )
    
    return v
}

function ffa(string media_file, string "source_dir", string "cache_dir", bool "cache", int "track"){
    source_dir = Defined(source_dir) ? source_dir : setGlobPath("glob_source_dir")
    cache_dir = Defined(cache_dir) ? cache_dir : setGlobPath("glob_cache_dir")
    cachefile = cache_dir + media_file + ".ffindex"
    cache = Default(cache, true)
    
    track = Default(track, -1)
    
    v = FFAudioSource(
        \ source_dir + media_file,
        \ track = track,
        \ cachefile = cachefile,
        \ cache = cache
        \ )
    
    return v
}

function videoAddPadMod2(clip c) {
    pr = c.Width() % 2 == 0 ? 0 : 1
    pb = c.Height() % 2 == 0 ? 0 : 1
    c = c.AddBorders(0, 0, pr, pb, color=$00000000)
    return c
}
