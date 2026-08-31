from motions.common import K, L, T, make

layers = (L("vertical", polygon=((.43,.06),(.57,.06),(.57,.94),(.43,.94)), z=1), L("horizontal", polygon=((.06,.43),(.94,.43),(.94,.57),(.06,.57)), z=2))
tracks = (
    T("vertical", (K(0), K(12, sx=.88, sy=1.25, easing="out_back"), K(24, sx=1.05, sy=.92), K(38), K(59))),
    T("horizontal", (K(0), K(12, sx=.88, sy=1.05), K(24, sx=1.23, sy=.90, easing="out_back"), K(38), K(59))),
)
SPEC = make("05-star-four", layers, tracks, "impact")
