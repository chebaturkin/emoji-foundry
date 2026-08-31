from motions.common import K, L, T, make

layers = (
    L("vertical", polygon=((.43,.08),(.57,.08),(.58,.92),(.42,.92)), z=1),
    L("horizontal", polygon=((.08,.42),(.92,.42),(.92,.58),(.08,.58)), z=2),
    L("rays", bbox=(.10,.10,.90,.90), z=3),
)
tracks = (
    T("base", (K(0, opacity=0), K(59, opacity=0))),
    T("vertical", (K(0), K(8, sx=.15, sy=1.18), K(18, sx=1.05, sy=.96, easing="out_back"), K(30), K(59))),
    T("horizontal", (K(0), K(8, sx=1.18, sy=.15), K(18, sx=.96, sy=1.05, easing="out_back"), K(30), K(59))),
    T("rays", (K(0), K(6), K(12, opacity=0, sx=.7, sy=.7), K(21, sx=1.16, sy=1.16, easing="out_back"), K(32), K(59))),
)
SPEC = make("06-spark", layers, tracks, "impact")
