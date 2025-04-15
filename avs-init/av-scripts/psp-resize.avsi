function resize4psp(clip c, int "pspSize"){
    pspSize = Default(pspSize, 1)
    if(pspSize < 1 || pspSize > 4){
        pspSize = 1
    }
    
    if(pspSize == 1){
        width = 480
        height = 272
        noBorders = true
    }
    if(pspSize == 2){
        width = 640
        height = 480
        noBorders = false
    }
    if(pspSize == 3){
        width = 720
        height = 480
        noBorders = false
    }
    if(pspSize == 4){
        width = 720
        height = 576
        noBorders = false
    }
    
    ratioS = Float(width(c))/Float(height(c))
    ratioD = Float(width)/Float(height)
    newWmod = Round(height*ratioS/2)*2
    newHmod = Round(width/ratioS/2)*2
    newW = newWmod%2 > 0 ? newWmod-1 : newWmod
    newH = newHmod%2 > 0 ? newHmod-1 : newHmod
    
    border_w = (width-newW)/2
    border_h = (height-newH)/2
    BorderW = noBorders == true || border_w < 1 ? 0 : border_w
    BorderH = noBorders == true || border_h < 1 ? 0 : border_h
    
    if ( pspSize == 1 && width(c)%16 == 0 && height(c)%9 == 0 ){
        c = Spline36Resize(c, 480, 272)
    }
    else{
        if ( BorderH%2 > 0 || BorderW%2 > 0 ){ c = c.convertToYUY2() }
        c = (ratioS>ratioD) ? c.Spline36Resize(width,newH).AddBorders(0, BorderH, 0, BorderH) : c
        c = (ratioS<ratioD) ? c.Spline36Resize(newW,height).AddBorders(BorderW, 0, BorderW, 0) : c
        c = (ratioS==ratioD) ? c.Spline36Resize(width,height) : c
        if ( BorderH%2 > 0 || BorderW%2 > 0 ){ c = c.convertToYV12() }
    }
    
    return c
}

function thumb4psp(clip c){
    minSize = min(float(160)/Width(c),float(120)/Height(c))
    c = c.trim(FrameCount(c)/2,FrameCount(c)/2).convertToRGB24()
    newWmod = Round(Width(c)*minSize)
    newHmod = Round(Height(c)*minSize)
    newW = newWmod%2 == 0 ? newWmod : newWmod-1
    newH = newHmod%2 == 0 ? newHmod : newHmod-1
    c = c.Spline36Resize(newW,newH)
    border_w = (160-Width(c))/2
    border_h = (120-Height(c))/2
    c = c.AddBorders(border_w,border_h,border_w,border_h)
    return c
}
