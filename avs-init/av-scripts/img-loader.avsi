# 1 fps    → 1000.000 ms/frame (mspf, ms per frame)
# 2 fps    →  500.000 ms/frame
# 4 fps    →  250.000 ms/frame
# 5 fps    →  200.000 ms/frame
# 8 fps    →  125.000 ms/frame
# 10 fps   →  100.000 ms/frame
# 20 fps   →   50.000 ms/frame
# 25 fps   →   40.000 ms/frame
# 40 fps   →   25.000 ms/frame
# 50 fps   →   20.000 ms/frame
# 100 fps  →   10.000 ms/frame

# 25fps = 1000ms / 40mspf
# base_fps = float(1000) / float(40)
# v = LoadFrameImage("./frames/000000.jpg", base_fps, 5)

#VideoFPS = float(1000) / float(32)
#ImageSource("./frames/%06d.jpg", start=0, end=149, fps=VideoFPS, pixel_type="RGB32")
#ConvertToPlanarRGB()
#ConvertToYUV420()

function LoadFrameImage(string file, float fps, int repeats) {
    img = ImageSource(file, start=0, end=0, fps=fps, pixel_type="RGB32")
    return img.Loop(repeats)
}
