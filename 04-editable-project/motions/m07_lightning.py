from motions.common import K, T, make

layers = ()
tracks = (
    T("root", (K(0), K(6, x=-2, y=-2, sx=.90, sy=.96, rotation=-5), K(11, x=3, y=2, sx=1.10, sy=1.04, rotation=6), K(16, x=-2, y=-1, sx=.96, sy=1.08, rotation=-4), K(22, x=1, sx=1.04, sy=.98, rotation=2, easing="out_back"), K(34), K(59))),
)
SPEC = make("07-lightning", layers, tracks, "impact")
