from motions.common import K, T, make

layers = ()
tracks = (
    T("root", (K(0), K(7, y=2, sx=.92, sy=.94, rotation=4), K(14, y=-4, sx=1.09, sy=1.10, rotation=-4, easing="out_back"), K(21, y=1, sx=.97, sy=.98, rotation=2), K(28, y=-1, sx=1.02, sy=1.02, rotation=-1), K(37), K(59))),
)
SPEC = make("09-idea", layers, tracks, "story")
