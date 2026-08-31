from motions.m01_heart import SPEC as m01
from motions.m02_heart_double import SPEC as m02
from motions.m03_heart_open import SPEC as m03
from motions.m04_star import SPEC as m04
from motions.m05_star_four import SPEC as m05
from motions.m06_spark import SPEC as m06
from motions.m07_lightning import SPEC as m07
from motions.m08_lightning_round import SPEC as m08
from motions.m09_idea import SPEC as m09
from motions.m10_bulb_spark import SPEC as m10
from motions.m11_eye import SPEC as m11
from motions.m12_smile import SPEC as m12
from motions.m13_laugh import SPEC as m13
from motions.m14_sad import SPEC as m14
from motions.m15_surprise import SPEC as m15
from motions.m16_like import SPEC as m16
from motions.m17_dislike import SPEC as m17
from motions.m18_question import SPEC as m18
from motions.m19_exclamation import SPEC as m19
from motions.m20_check import SPEC as m20
from motions.m21_cross import SPEC as m21
from motions.m22_favorite import SPEC as m22
from motions.m23_launch import SPEC as m23
from motions.m24_explosion_ray import SPEC as m24
from motions.m25_explosion_cloud import SPEC as m25
from motions.m26_explosion_ring import SPEC as m26
from frame_motions.registry import FRAME_SPECS

SPECS = {spec.stem: spec for spec in (
    m01, m02, m03, m04, m05, m06, m07, m08, m09, m10, m11, m12, m13,
    m14, m15, m16, m17, m18, m19, m20, m21, m22, m23, m24, m25, m26,
)}
SPECS.update(FRAME_SPECS)
