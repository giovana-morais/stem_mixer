import pytest
import os

from preprocessing import brid_track_info, musdb_track_info, stems_from_file
import metadata

BRID_INDEX = "brid_index.txt"
MUSDB_INDEX = "musdb_index.txt"


@pytest.fixture
def data_home():
    return "/test/path"


@pytest.mark.parametrize("tid, expected_metadata", [
    ("1234 MX-PD-SA.wav", {
        "stem_name": "1234 MX-PD-SA.wav",
        "data_home": "/test/path",
        "tempo": 80.0,
        "key": None,
        "sound_class": "percussive",
        "instrument_name": "pandeiro",
    }),
    ("5678 MX-TB-PA.wav", {
        "stem_name": "5678 MX-TB-PA.wav",
        "data_home": "/test/path",
        "tempo": 100.0,
        "key": None,
        "sound_class": "percussive",
        "instrument_name": "tamborim",
    }),
    ("9123 MX-RR-SE.wav", {
        "stem_name": "9123 MX-RR-SE.wav",
        "data_home": "/test/path",
        "tempo": 130.0,
        "key": None,
        "sound_class": "percussive",
        "instrument_name": "reco-reco",
    })
])


def test_brid_track_info(data_home, tid, expected_metadata):
    result = brid_track_info(data_home, tid)
    assert result == expected_metadata


@pytest.mark.parametrize("tid, expected_metadata", [
    ("Artist - Track - drums.wav", {
        "stem_name": "Artist - Track - drums.wav",
        "data_home": "/test/path",
        "tempo": None,
        "key": None,
        "sound_class": "percussive",
        "instrument_name": "drums",
    }),
    ("Artist - Track - vocals.wav", {
        "stem_name": "Artist - Track - vocals.wav",
        "data_home": "/test/path",
        "tempo": None,
        "key": None,
        "sound_class": "vocals",
        "instrument_name": "vocals",
    }),
    ("Artist - Track - other.wav", {
        "stem_name": "Artist - Track - other.wav",
        "data_home": "/test/path",
        "tempo": None,
        "key": None,
        "sound_class": "harmonic",
        "instrument_name": None,
    }),
    ("Artist - Track - bass.wav", {
        "stem_name": "Artist - Track - bass.wav",
        "data_home": "/test/path",
        "tempo": None,
        "key": None,
        "sound_class": "harmonic",
        "instrument_name": "bass",
    })
])


def test_musdb_track_info(data_home, tid, expected_metadata):
    result = musdb_track_info(data_home, tid)
    assert result == expected_metadata


@pytest.mark.parametrize("file_path", 
    [BRID_INDEX, MUSDB_INDEX])

def test_stems_from_file(file_path):
    with open(file_path, 'r') as f:
        expected_stems = f.read().splitlines()
    result = stems_from_file(file_path)
    assert result == expected_stems
