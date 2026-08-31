from motions.common import K, L, P, STEEL, T, make

layers = (
    L("left_eye", bbox=(.30,.28,.49,.50), colors=(STEEL,), fill=P, z=2),
    L("right_eye", bbox=(.51,.28,.70,.50), colors=(STEEL,), fill=P, z=2),
    L("mouth", bbox=(.25,.47,.75,.76), colors=(STEEL,), fill=P, z=3),
)
tracks = (
    T("root", (K(0), K(8, y=4, sy=.96), K(17, y=-3, sy=1.04, easing="out_back"), K(28), K(59))),
    T("left_eye", (K(0), K(7, sy=.15), K(12, sy=1.04), K(22), K(59))),
    T("right_eye", (K(0), K(9, sy=.15), K(14, sy=1.04), K(24), K(59))),
    T("mouth", (K(0), K(10, sx=.94), K(18, sx=1.16, sy=1.08, easing="out_back"), K(30), K(59))),
)
SPEC = make("12-smile", layers, tracks, "soft")
