from motions.common import K, L, T, make

layers = (L("center", bbox=(.28,.27,.72,.73), z=2), L("rays", bbox=(.08,.08,.92,.92), z=1))
tracks = (
    T("center", (K(0), K(7, sx=.72, sy=.72), K(14, sx=1.24, sy=1.24, easing="out_back"), K(21, sx=.92, sy=.92), K(27, sx=1.08, sy=1.08), K(38), K(59))),
    T("rays", (K(0), K(9, sx=.78, sy=.78, rotation=-5), K(17, sx=1.20, sy=1.20, rotation=4, easing="out_back"), K(25, sx=.95, sy=.95), K(39), K(59))),
)
SPEC = make("24-explosion-ray", layers, tracks, "impact")
