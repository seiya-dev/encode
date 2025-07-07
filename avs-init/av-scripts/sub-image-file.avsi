# https://github.com/Asd-g/AviSynthPlus-SubImageFile

function BlendSubImage(clip c, string file, bool "info", string "matrix", string "transfer", string "primaries"){
    Assert(!IsRGB(c), "BlendSubImage: clip must be in YUV format.")
    
    info_ = Default(info, false)
    matrix = Default(matrix, "709")
    transfer = Default(transfer, "709")
    primaries = Default(primaries, "709")
    
    info_ = info_ ? true : false
    subs = SubImageFile(c, file, info=info_)
    alpha = PropToClip(subs)
    
    colorspace_op_param = Format("rgb:{transfer}:{primaries}=>{matrix}:{transfer}:{primaries}")
    Layer(BlankClip(alpha), z_ConvertFormat(subs, pixel_type="y8", colorspace_op=colorspace_op_param))
    mt_merge(BlankClip(last), last, alpha)
    
    premultiplied = z_ConvertFormat(last, Width(c), Height(c), pixel_type=PixelType(c), resample_filter="bicubic")
    alpha = z_ConvertFormat(alpha, Width(c), Height(c), pixel_type=PixelType(c), resample_filter="bicubic")
    mt_merge(c, premultiplied, alpha, luma=true)
    
    if (info_){
        current_frame = 0
        Text(propGetString(subs, "text"), text_color=color_khaki)
    }
}
