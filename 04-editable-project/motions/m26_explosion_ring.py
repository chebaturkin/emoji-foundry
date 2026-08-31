from motions.common import K, L, T, make

layers = (L("inner", bbox=(.29,.29,.71,.71), z=2), L("outer", bbox=(.08,.08,.92,.92), z=1))
tracks = (
    T("base", (K(0, opacity=0), K(59, opacity=0))),
    T("inner", (K(0), K(8, sx=.70, sy=.70), K(20, sx=1.12, sy=1.12, easing="out_back"), K(36), K(59))),
    T("outer", (K(0), K(8, sx=.90, sy=.90), K(16, sx=1.22, sy=1.22, easing="out_back"), K(25, sx=.94, sy=.94), K(38), K(59))),
)
SPEC = make("26-explosion-ring", layers, tracks, "impact")
