import pytest
import os

import metadata

print(os.getcwd())

@pytest.mark.parametrize(
	"stem_path", ["tests/Music Delta - Rockabilly-other.wav", "tests/[0257] S2-SK2-01-SA.wav"], 
	"expected_sc", ["harmonic", "percussive"]
	)

def test_get_sound_class(stem_path, expected_sc):
	sound_class = get_sound_class(stem_path)
	assert sound_class == expected_sc
