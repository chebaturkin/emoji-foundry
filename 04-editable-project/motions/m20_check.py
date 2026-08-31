from motions.common import K, L, STEEL, T, make

layers = (L("check", bbox=(.28,.30,.72,.72), colors=(STEEL,), polygon=((.28,.48),(.45,.68),(.74,.28),(.80,.36),(.46,.80),(.22,.56)), z=2),)
tracks = (
    T("base", (K(0, reveal=0), K(24, reveal=1), K(47, reveal=1), K(59, reveal=0)), reveal_mode="clockwise"),
    T("check", (K(0, reveal=0), K(18, reveal=0), K(34, reveal=1), K(38, sx=1.08, sy=1.08, easing="out_back"), K(45), K(48, reveal=1), K(59, reveal=0)), reveal_mode="left_to_right"),
)
SPEC = make("20-check", layers, tracks, "story")
