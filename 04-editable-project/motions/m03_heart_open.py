from motions.common import K, L, STEEL, T, make

layers = (L("opening", bbox=(.50,.62,.70,.91), colors=(STEEL,), fill=(0,0,0,0), z=2),)
tracks = (
    T("opening", (K(0), K(15, x=-3, y=1, sx=.90, rotation=-3), K(23, x=3, y=-1, sx=1.06, rotation=3, easing="out_back"), K(38), K(59))),
    T("root", (K(0), K(15, sx=.95, sy=1.02), K(23, sx=1.03, sy=.98, easing="out_back"), K(38), K(59))),
)
SPEC = make("03-heart-open", layers, tracks, "soft")
