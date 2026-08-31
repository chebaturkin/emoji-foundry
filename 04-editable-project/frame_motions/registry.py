from frame_motions.m01_heart import SPEC as heart
from frame_motions.m02_heart_double import SPEC as heart_double
from frame_motions.m03_heart_open import SPEC as heart_open
from frame_motions.m04_star import SPEC as star
from frame_motions.m05_star_four import SPEC as star_four
from frame_motions.m06_spark import SPEC as spark
from frame_motions.m07_lightning import SPEC as lightning
from frame_motions.m08_lightning_round import SPEC as lightning_round
from frame_motions.m09_idea import SPEC as idea
from frame_motions.m10_bulb_spark import SPEC as bulb_spark
from frame_motions.m11_eye import SPEC as eye
from frame_motions.m12_smile import SPEC as smile
from frame_motions.m13_laugh import SPEC as laugh
from frame_motions.m14_sad import SPEC as sad
from frame_motions.m15_surprise import SPEC as surprise
from frame_motions.m16_like import SPEC as like
from frame_motions.m17_dislike import SPEC as dislike
from frame_motions.m18_question import SPEC as question
from frame_motions.m19_exclamation import SPEC as exclamation
from frame_motions.m20_check import SPEC as check
from frame_motions.m21_cross import SPEC as cross
from frame_motions.m22_favorite import SPEC as favorite
from frame_motions.m23_launch import SPEC as launch
from frame_motions.m24_explosion_ray import SPEC as explosion_ray
from frame_motions.m25_explosion_cloud import SPEC as explosion_cloud
from frame_motions.m26_explosion_ring import SPEC as explosion_ring
from frame_motions.m27_ira_heart import SPEC as ira_heart


FRAME_SPECS = {
    spec.stem: spec
    for spec in (
        heart,
        heart_double,
        heart_open,
        star,
        star_four,
        spark,
        lightning,
        lightning_round,
        idea,
        bulb_spark,
        eye,
        smile,
        laugh,
        sad,
        surprise,
        like,
        dislike,
        question,
        exclamation,
        check,
        cross,
        favorite,
        launch,
        explosion_ray,
        explosion_cloud,
        explosion_ring,
        ira_heart,
    )
}
