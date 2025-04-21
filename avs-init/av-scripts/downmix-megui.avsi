# 5.1 Channels L,R,C,LFE,SL,SR -> stereo + LFE
function c6_stereo(clip a) {
    fl = GetChannel(a, 1)
    fr = GetChannel(a, 2)
    fc = GetChannel(a, 3)
    lf = GetChannel(a, 4)
    sl = GetChannel(a, 5)
    sr = GetChannel(a, 6)
    fl_sl = MixAudio(fl, sl, 0.2929, 0.2929)
    fr_sr = MixAudio(fr, sr, 0.2929, 0.2929)
    fc_lf = MixAudio(fc, lf, 0.2071, 0.2071)
    l = MixAudio(fl_sl, fc_lf, 1.0, 1.0)
    r = MixAudio(fr_sr, fc_lf, 1.0, 1.0)
    return MergeChannels(l, r)
}

# 5 Channels L,R,C,SL,SR or L,R,LFE,SL,SR-> Stereo
function c5_stereo(clip a) {
    fl = GetChannel(a, 1)
    fr = GetChannel(a, 2)
    fc = GetChannel(a, 3)
    sl = GetChannel(a, 4)
    sr = GetChannel(a, 5)
    fl_sl = MixAudio(fl, sl, 0.3694, 0.3694)
    fr_sr = MixAudio(fr, sr, 0.3694, 0.3694)
    l = MixAudio(fl_sl, fc, 1.0, 0.2612)
    r = MixAudio(fr_sr, fc, 1.0, 0.2612)
    return MergeChannels(l, r)
}

# 5 Channels L,R,C,LFE,S -> Stereo
function c52_stereo(clip a) {
    fl = GetChannel(a, 1)
    fr = GetChannel(a, 2)
    fc = GetChannel(a, 3)
    lf = GetChannel(a, 4)
    bc = GetChannel(a, 5)
    fl_bc = MixAudio(fl, bc, 0.3205, 0.2265)
    fr_bc = MixAudio(fr, bc, 0.3205, 0.2265)
    fc_lf = MixAudio(fc, lf, 0.2265, 0.2265)
    l = MixAudio(fl_bc, fc_lf, 1.0, 1.0)
    r = MixAudio(fr_bc, fc_lf, 1.0, 1.0)
    return MergeChannels(l, r)
}

# 4 Channels Quadro L,R,SL,SR -> Stereo
function c4_stereo(clip a) {
    fl = GetChannel(a, 1)
    fr = GetChannel(a, 2)
    sl = GetChannel(a, 3)
    sr = GetChannel(a, 4)
    l = MixAudio(fl, sl, 0.5, 0.5)
    r = MixAudio(fr, sr, 0.5, 0.5)
    return MergeChannels(l, r)
}

# 4 Channels L,R,C,LFE or L,R,S,LFE or L,R,C,S -> Stereo
function c42_stereo(clip a) {
    fl = GetChannel(a, 1)
    fr = GetChannel(a, 2)
    fc = GetChannel(a, 3)
    lf = GetChannel(a, 4)
    fc_lf = MixAudio(fc, lf, 0.2929, 0.2929)
    l = MixAudio(fl, fc_lf, 0.4142, 1.0)
    r = MixAudio(fr, fc_lf, 0.4142, 1.0)
    return MergeChannels(l, r)
}

# 3 Channels L,R,C or L,R,S or L,R,LFE -> Stereo
function c3_stereo(clip a) {
    fl = GetChannel(a, 1)
    fr = GetChannel(a, 2)
    fc = GetChannel(a, 3)
    l = MixAudio(fl, fc, 0.5858, 0.4142)
    r = MixAudio(fr, fc, 0.5858, 0.4142)
    return MergeChannels(l, r)
}
