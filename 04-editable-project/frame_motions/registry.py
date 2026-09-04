from frame_motions.m01_heart import SPEC as heart
from frame_motions.m02_heart_double import SPEC as heart_double
from frame_motions.m03_heart_open import SPEC as heart_open
from frame_motions.m27_ira_heart import SPEC as ira_heart


FRAME_SPECS = {
    spec.stem: spec
    for spec in (heart, heart_double, heart_open, ira_heart)
}
