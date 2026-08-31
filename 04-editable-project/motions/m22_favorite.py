from motions.common import K, L, P, PARCHMENT, T, make

layers = (L("dash", bbox=(.36,.26,.64,.39), colors=(PARCHMENT,), fill=(0,0,0,0), z=3),)
tracks = (
    T("root", (K(0), K(11, y=5, sy=.88, sx=1.04), K(20, y=-2, sy=1.08, sx=.98, easing="out_back"), K(34), K(59))),
    T("dash", (K(0), K(5), K(8, x=-3, sx=.86), K(22, x=0, sx=1.08, easing="out_back"), K(34), K(59))),
)
SPEC = make("22-favorite", layers, tracks, "soft")
