from motions.common import K, L, T, make

layers = (L("dot", bbox=(.36,.66,.64,.88), z=2),)
tracks = (
    T("root", (K(0), K(10, y=5, sy=.86, sx=1.05), K(18, y=-3, sy=1.12, sx=.97, easing="out_back"), K(30), K(59))),
    T("dot", (K(0), K(8), K(13, y=3, sy=.85), K(20, y=-2, sy=1.12, easing="out_back"), K(30), K(59))),
)
SPEC = make("19-exclamation", layers, tracks, "story")
