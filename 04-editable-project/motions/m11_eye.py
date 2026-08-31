from motions.common import K, L, OBSIDIAN, P, STEEL, T, make

layers = (L("pupil", bbox=(.36,.31,.64,.68), colors=(OBSIDIAN, STEEL), fill=P, z=2), L("lid", bbox=(.12,.22,.88,.77), z=1))
tracks = (
    T("root", (K(0), K(59))),
    T("lid", (K(0), K(8, sy=.08), K(15, sy=1.04, easing="out_back"), K(24), K(59))),
    T("pupil", (K(0), K(15), K(22, x=5, sx=.9), K(29, x=-2, sx=1.04), K(38), K(59))),
)
SPEC = make("11-eye", layers, tracks, "story")
