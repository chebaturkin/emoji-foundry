from motions.common import K, L, T, make

layers = (L("body", bbox=(.31,.10,.69,.70), z=2), L("wings", bbox=(.18,.45,.82,.78), z=1), L("tail", bbox=(.34,.67,.66,.93), z=3))
tracks = (
    T("root", (K(0), K(8, y=5, sy=.93), K(18, y=-8, sy=1.12, easing="out_back"), K(30, y=1, sy=.98), K(42), K(59))),
    T("body", (K(0), K(8, sy=.90), K(18, sy=1.16), K(29, sy=.96), K(42), K(59))),
    T("wings", (K(0), K(11, sy=.92), K(21, sy=1.10), K(34), K(59))),
    T("tail", (K(0), K(8, sy=.9), K(18, y=3, sy=1.28), K(29, sy=.90), K(42), K(59))),
)
SPEC = make("23-launch", layers, tracks, "story")
