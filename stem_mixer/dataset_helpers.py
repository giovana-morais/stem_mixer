#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. autosummary::
   :toctree: generated/

   parse_musdb
"""
import os

import soundfile as sf
import tqdm

def parse_musdb(data_home, output_folder):
    r"""
    Process musdb .mp4 tracks and save as separate .wav stem tracks

    Parameters
    ----------
    data_home : str
        data home for the unzipped musdb dataset
    output_folder : str
        output
    """
    import musdb
    mus = musdb.DB(root=data_home)

    stems = ["bass", "drums", "other", "vocals"]
    output_folder = "stems"

    os.makedirs(output_folder, exist_ok=True)

    for track in tqdm.tqdm(mus):
        track_name = track

        for target in stems:
            stem_audio = track.targets[target].audio
            stem_name = f"{track_name} - {target}.wav"
            stem_path = os.path.join(output_folder, stem_name)

            sf.write(stem_path, stem_audio, track.rate)
