#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. autosummary::
   :toctree: generated/

   tempo
   tempo_bin
   sound_class
"""
import math

import librosa
import numpy as np

DEFAULT_SR = 44100


def tempo(stem_path):
    r"""
    Extracts the tempo from an audio stem file.

    Parameters
    ----------
    stem_path : str
        path to the audio stem file.

    Returns
    -------
    tempo : float
        The estimated tempo of the audio file.
    """

    audio_file, sr = librosa.load(stem_path, sr=DEFAULT_SR, mono=True)
    tempo, _ = librosa.beat.beat_track(y=audio_file, sr=sr)
    tempo = float(tempo)

    return tempo


def tempo_bin(tempo):
    r"""
    Given a tempo value, return what is the tempo bin it pertains

    Parameters
    ----------
    tempo : float

    Returns
    -------
    tempo_bin : int
    """
    return math.ceil(tempo / 5) * 5


def sound_class(stem_path):
    r"""
    Extracts the sound class (harmonic / percussive) from an audio stem file.

    Parameters
    ----------
    stem_path : str
        path to the audio stem file.

    Returns
    -------
    sound_class : str
        The determined sound class of the audio file, or "undetermined"
        if difference between percussive / harmonic is not significant enough
    """

    y, sr = librosa.load(stem_path, sr=DEFAULT_SR, mono=True)
    harmonic, percussive = librosa.effects.hpss(y)

    harmonic_energy = np.sqrt(np.mean(np.square(harmonic)))
    percussive_energy = np.sqrt(np.mean(np.square(percussive)))

    percent_difference = abs(harmonic_energy - percussive_energy) / (
        (harmonic_energy + percussive_energy) / 2
    )

    threshold = 0.50  # 50% THRESHOLD (subject to change)

    if percent_difference < threshold:
        sound_class = "undetermined"
    elif percussive_energy > harmonic_energy:
        sound_class = "percussive"
    else:
        sound_class = "harmonic"

    return sound_class
