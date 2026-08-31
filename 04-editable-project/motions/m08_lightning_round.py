from motions.common import K, T, make

layers = ()
tracks = (
    T("root", (K(0), K(7, rotation=9, x=3, y=-2, sx=.94, sy=1.04), K(13, rotation=-10, x=-3, y=2, sx=1.07, sy=.96), K(19, rotation=6, x=2, y=-1), K(26, rotation=-2, x=-1, easing="out_back"), K(38), K(59))),
)
SPEC = make("08-lightning-round", layers, tracks, "impact")
