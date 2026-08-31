from motions.common import K, T, make

SPEC = make("01-heart", (), (T("root", (K(0), K(7, sx=.94, sy=1.06), K(12, sx=1.12, sy=.92, rotation=-3, easing="out_back"), K(18), K(24, sx=.97, sy=1.03), K(29, sx=1.07, sy=.96, rotation=2), K(38), K(59))),), "soft")
