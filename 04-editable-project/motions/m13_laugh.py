from motions.common import K, T, make

layers = ()
tracks = (
    T("root", (K(0), K(7, y=2, sx=1.05, sy=.90, rotation=-2), K(12, y=-4, sx=.96, sy=1.10, rotation=2, easing="out_back"), K(18, y=1, sx=1.04, sy=.92, rotation=-1), K(24, y=-3, sx=.97, sy=1.07, rotation=1, easing="out_back"), K(34), K(59))),
)
SPEC = make("13-laugh", layers, tracks, "soft")
