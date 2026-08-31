from motions.common import K, T, make

layers = ()
tracks = (
    T("root", (K(0), K(6, sx=.97, sy=.97, rotation=-2), K(11, sx=.84, sy=.84, rotation=-7), K(19, sx=1.12, sy=1.12, rotation=4, easing="out_back"), K(27, sx=.98, sy=.98, rotation=-1), K(37), K(59))),
)
SPEC = make("10-bulb-spark", layers, tracks, "story")
