from motions.common import K, L, PARCHMENT, STEEL, T, TAUPE, make

layers = (
    L("outer", colors=(STEEL,), tolerance=55, z=1),
    L("inner", colors=(TAUPE, PARCHMENT), tolerance=45, z=2),
)
tracks = (
    T("base", (K(0, opacity=0), K(59, opacity=0))),
    T("outer", (K(0, reveal=0), K(25, reveal=1), K(43, reveal=1), K(59, reveal=0)), reveal_mode="clockwise", reveal_origin=(.5,.52)),
    T("inner", (K(0, reveal=0), K(7, reveal=0), K(31, reveal=1), K(43, reveal=1), K(56, reveal=0), K(59, reveal=0)), reveal_mode="clockwise", reveal_origin=(.5,.52)),
    T("root", (K(0), K(31), K(37, sx=1.025, sy=1.025), K(43), K(59))),
)
SPEC = make("02-heart-double", layers, tracks, "soft")
