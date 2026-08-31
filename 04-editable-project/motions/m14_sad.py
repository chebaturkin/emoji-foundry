from motions.common import K, L, P, STEEL, T, make

layers = (L("eyes", bbox=(.25,.28,.75,.48), colors=(STEEL,), fill=P, z=2), L("mouth", bbox=(.25,.51,.75,.75), colors=(STEEL,), fill=P, z=3))
tracks = (
    T("root", (K(0), K(14, y=5, sy=.97), K(24, y=7, sy=.94), K(42), K(59))),
    T("eyes", (K(0), K(18, y=3, sy=.9), K(38), K(59))),
    T("mouth", (K(0), K(20, y=3, sy=1.12), K(42), K(59))),
)
SPEC = make("14-sad", layers, tracks, "soft")
