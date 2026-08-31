from motions.common import K, L, OBSIDIAN, P, STEEL, T, make

layers = (L("eyes", bbox=(.25,.25,.75,.50), colors=(OBSIDIAN, STEEL), fill=P, z=2), L("mouth", bbox=(.34,.48,.66,.78), colors=(OBSIDIAN, STEEL), fill=P, z=3))
tracks = (
    T("root", (K(0), K(7, sx=.90, sy=1.06), K(15, sx=1.06, sy=.96, easing="out_back"), K(30), K(59))),
    T("eyes", (K(0), K(12, sx=1.24, sy=1.24, easing="out_back"), K(22, sx=.96, sy=.96), K(34), K(59))),
    T("mouth", (K(0), K(12, sx=1.22, sy=1.28, easing="out_back"), K(22, sx=.94, sy=.94), K(34), K(59))),
)
SPEC = make("15-surprise", layers, tracks, "soft")
