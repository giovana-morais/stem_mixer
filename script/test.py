import pytest
import json
import os
from script import preprocessing

@pytest.fixture

def temp_dir(tmpdir):
    """Fixture to create a temporary directory for testing."""
    temp_dir = tmpdir.mkdir("test_dir")
    yield temp_dir

def test_brid(temp_dir):

    # test BRID file
    file_path = os.path.join(temp_dir, "test-PD01-CA.wav")
    tempo, instrument_name, key, sound_class = brid(file_path)

    assert tempo == 65.1
    assert instrument_name == "pandeiro"
    assert key is None
    assert sound_class == "percussive"