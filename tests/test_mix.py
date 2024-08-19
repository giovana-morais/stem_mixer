import pytest

import numpy as np

from stem_mixer.mix import normalize
from stem_mixer.metadata import dict_template



def test_normalize():
    s1 = dict_template("data_home", "track1")
    s1["audio"] = np.ones(10)

    s2 = dict_template("data_home", "track2")
    s2["audio"] = np.ones(10)*2

    s3 = dict_template("data_home", "track3")
    s3["audio"] = np.ones(10)*3

    stems = [s1, s2, s3]

    stems = normalize(stems)

    for s in stems:
        np.testing.assert_allclose(s["audio"], np.ones(10), rtol=1e-8, atol=0)

    return
