from motions.common import K, L, STEEL, T, make

layers = (
    L("slash_a", bbox=(.28,.28,.72,.72), colors=(STEEL,), polygon=((.28,.35),(.35,.28),(.72,.65),(.65,.72)), z=2),
    L("slash_b", bbox=(.28,.28,.72,.72), colors=(STEEL,), polygon=((.65,.28),(.72,.35),(.35,.72),(.28,.65)), z=3),
)
tracks = (
    T("base", (K(0), K(21, sx=.90, sy=.90), K(29, sx=1.06, sy=1.06, easing="out_back"), K(40), K(59))),
    T("slash_a", (K(0), K(3), K(5, x=-5, rotation=-8, opacity=0), K(18, x=0, rotation=0, opacity=1, easing="out_back"), K(59))),
    T("slash_b", (K(0), K(4), K(7, x=5, rotation=8, opacity=0), K(20, x=0, rotation=0, opacity=1, easing="out_back"), K(59))),
)
SPEC = make("21-cross", layers, tracks, "story")
