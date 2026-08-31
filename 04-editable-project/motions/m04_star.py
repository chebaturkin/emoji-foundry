from motions.common import K, T, make

layers = ()
tracks = (T("root", (K(0), K(7, sx=.78, sy=.78, rotation=-8), K(17, sx=1.12, sy=1.12, rotation=5, easing="out_back"), K(25, sx=.98, sy=.98, rotation=-2), K(34), K(59))),)
SPEC = make("04-star", layers, tracks, "impact")
