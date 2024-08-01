import pytest
import os

from metadata import get_sound_class

# NOTE: currently running this out of stem_mixer/script, might need to adjust paths later on

@pytest.mark.parametrize(
    "stem_path, expected_sc", 
    [
        ("../tests/Music Delta - Rockabilly-other.wav", "harmonic"), 
        ("../tests/[0257] S2-SK2-01-SA.wav", "percussive")
    ]
)

def test_get_sound_class(stem_path, expected_sc):
	sound_class = get_sound_class(stem_path)
	assert sound_class == expected_sc
