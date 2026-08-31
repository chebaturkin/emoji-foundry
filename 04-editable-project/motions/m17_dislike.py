from motions.common import K, L, TAUPE, T, T_FILL, make

layers = (L("cuff", bbox=(.14,.17,.42,.47), colors=(TAUPE,), fill=T_FILL, z=2),)
tracks = (
    T("root", (K(0), K(9, y=-2, rotation=4), K(17, y=7, rotation=-10, easing="out_back"), K(25, y=-1, rotation=3), K(38), K(59))),
    T("cuff", (K(0), K(11, y=-2, rotation=2), K(19, y=4, rotation=-4), K(29), K(59))),
)
SPEC = make("17-dislike", layers, tracks, "soft")
