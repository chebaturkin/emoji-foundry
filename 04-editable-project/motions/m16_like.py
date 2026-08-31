from motions.common import K, L, TAUPE, T, T_FILL, make

layers = (L("cuff", bbox=(.14,.53,.42,.83), colors=(TAUPE,), fill=T_FILL, z=2),)
tracks = (
    T("root", (K(0), K(7, y=4, rotation=-7), K(14, y=-6, rotation=8, easing="out_back"), K(22, y=1, rotation=-2), K(34), K(59))),
    T("cuff", (K(0), K(9, y=3, rotation=-3), K(16, y=-3, rotation=4), K(26), K(59))),
)
SPEC = make("16-like", layers, tracks, "soft")
