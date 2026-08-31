from motions.common import K, L, T, make

layers = (L("dot", bbox=(.38,.67,.62,.88), z=2),)
tracks = (
    T("root", (K(0), K(9, rotation=-8, x=-2), K(18, rotation=7, x=2, easing="out_back"), K(28, rotation=-2), K(40), K(59))),
    T("dot", (K(0), K(9, y=-6, sy=1.1), K(16, y=2, sy=.9, easing="out_back"), K(28), K(59))),
)
SPEC = make("18-question", layers, tracks, "story")
