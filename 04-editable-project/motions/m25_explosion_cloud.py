from motions.common import K, T, make

layers = ()
tracks = (T("root", (K(0), K(8, sx=.76, sy=.82, rotation=-4), K(15, sx=1.18, sy=1.14, rotation=3, easing="out_back"), K(21, sx=.95, sy=1.06, rotation=-2), K(29, sx=1.03, sy=.98), K(38), K(59))),)
SPEC = make("25-explosion-cloud", layers, tracks, "impact")
