import json
import math
import os

import librosa
import numpy as np

DEFAULT_SR = 44100


# is it better to have a class?
def dict_template(data_home=None, stem_name=None):
    """
    create empty metadata dictionary
    """

    metadata = {
        "stem_name": stem_name,
        "data_home": data_home,
        "tempo": None,
        "key": None,
        "sound_class": None,
    }

    return metadata


def extraction(stem_path, track_metadata=None, overwrite=False):
    """
    Takes file path to a stem and processes its metadata to save as JSON.

    Parameters:
        stem_path: str
            Path to the audio stem file.
        metadata: dict (optional)
            dictionary with pre-computed metadata
        overwrite: boolean
            if True, overwrite a JSON file that already exists

    Returns:
        None
    """

    json_file_path = os.path.splitext(stem_path)[0] + ".json"

    if track_metadata is None:
        track_metadata = dict_template()

    if not os.path.exists(json_file_path) or overwrite:
        metadata = track_metadata.copy()

        if metadata["tempo"] is None:
            # print("extracting tempo")
            metadata["tempo"] = get_tempo(stem_path)

        if metadata["sound_class"] is None:
            # print("extracting sound_class")
            metadata["sound_class"] = get_sound_class(stem_path)

        metadata["tempo_bin"] = (
            math.ceil(metadata["tempo"] / 5) * 5
        )  # adding tempo-bin to metadata

        with open(json_file_path, "w") as json_file:
            json.dump(metadata, json_file, indent=4)


def get_tempo(stem_path):
    """
    Extracts the tempo from an audio stem file.

    Parameters:
        stem_path (str): Path to the audio stem file.

    Returns:
        tempo (float): The estimated tempo of the audio file.
    """

    audio_file, sr = librosa.load(stem_path, sr=DEFAULT_SR, mono=True)
    tempo, _ = librosa.beat.beat_track(y=audio_file, sr=sr)
    tempo = float(tempo[0])

    return tempo


def get_sound_class(stem_path):
    """
    Extracts the sound class (harmonic / percussive) from an audio stem file.

    Parameters:
        stem_path (str): Path to the audio stem file.

    Returns:
        sound_class (str): The determined sound class of the audio file, or "undetermined"
        if difference between percussive / harmonic is not significant enough
    """

    audio_file, sr = librosa.load(stem_path, sr=DEFAULT_SR, mono=True)
    audio_norm = librosa.util.normalize(audio_file)
    harmonic, percussive = librosa.effects.hpss(audio_norm)

    harmonic_energy = np.sqrt(np.mean(np.square(harmonic)))
    percussive_energy = np.sqrt(np.mean(np.square(percussive)))

    percent_difference = abs(harmonic_energy - percussive_energy) / (
        (harmonic_energy + percussive_energy) / 2
    )

    threshold = 0.50  # 50% THRESHOLD (subject to change)

    if percent_difference > threshold:
        sound_class = (
            "percussive" if percussive_energy > harmonic_energy else "harmonic"
        )
    else:
        sound_class = "undetermined"  # don't want None because then it will keep looping trying to fill in

    return sound_class
