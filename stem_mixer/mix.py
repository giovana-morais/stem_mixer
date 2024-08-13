#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. autosummary::
   :toctree: generated/

   select_stems
   possible_tempo_bins
   time_stretch
   align_first_beat
   mix
   generate_mixtures
   save_mixture
"""
import argparse
import os
import json
import random
import uuid

import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import tqdm

DEFAULT_SR = 44100


def select_stems(
    n_percussive, n_harmonic, data_home, index_file, base_stem=None, **kwargs
):
    """
    Select stems from a given index

    Parameters
    -----------
    base_stem : str
    \*\*kwargs : dict additional arguments

    Returns
    -------
    stems : list[dict]
        list with stems that will be used for mixture
        each element of the list is a dictionary with the necessary
        information about that stem.
    base_tempo : int
        tempo_bin from the base stem
    """
    index = pd.read_csv(os.path.join(data_home, index_file))
    tempo_choices = possible_tempo_bins(index, n_harmonic, n_percussive)

    # print(tempo_choices)
    tempo = random.choice(tempo_choices)
    # print(tempo_choices, tempo)

    # base_stem for now is random if not provided
    if base_stem is not None:
        base_stem = index[index["stem_name"] == base_stem]
    elif n_percussive > 0:
        n_percussive -= 1
        base_stem = index[
            (index["sound_class"] == "percussive") & (index["tempo_bin"] == tempo)
        ].sample()
    elif n_harmonic > 0:
        n_harmonic -= 1
        base_stem = index[
            (index["sound_class"] == "harmonic") & (index["tempo_bin"] == tempo)
        ].sample()

    # remove base_stem from index so we don't use it twice
    index = index.drop(base_stem.index)

    base_stem = base_stem.to_dict("records")[0]
    base_tempo = base_stem["tempo_bin"]
    tempo_octaves = [int(i * base_tempo) for i in [0.5, 1, 2, 4]]

    index_filtered = index[
        (index["tempo_bin"].isin(tempo_octaves))
        & (index["instrument_name"] != base_stem["instrument_name"])
    ]

    # TODO: add instrument check

    # TODO: what to do with undetermined stems?
    # sample percussive stems
    percussive = []
    if n_percussive > 0:
        percussive_index = index_filtered[index_filtered["sound_class"] == "percussive"]
        # if len(percussive_index) < n_percussive:
        #     print("no percussive tracks left on this tempo bin!")
        percussive = percussive_index.sample(n_percussive).to_dict("records")

    # sample harmonic stems
    harmonic = []
    if n_harmonic > 0:
        harmonic_index = index_filtered[index_filtered["sound_class"] == "harmonic"]
        # if len(harmonic_index) < n_harmonic:
        #     print("no harmonic tracks left on this tempo bin!")
        harmonic = harmonic_index.sample(n_harmonic).to_dict("records")

    # combine everything into single list
    stems = [base_stem] + percussive + harmonic
    return stems, base_tempo


def possible_tempo_bins(index, n_harmonic, n_percussive):
    r"""
    return all possible tempo_bins that can be used for the provided n_harmonic and
    n_percussive

    Parameters
    ----------
    index : pd.DataFrame
        dataframe with stems information
    n_harmonic : int
        number of harmonic stems for a given mixture
    n_percussive : int
        number of percussive stems for a given mixture

    Returns
    -------
    possible_tempo : list
        list with tempo_bins that have at least n_harmonic and n_percussive
        tracks
    """

    all_tempo_bins = index["tempo_bin"].unique()
    tempo_bin_count = index[["tempo_bin", "sound_class"]].value_counts()

    possible_tempo = []

    for tempo in all_tempo_bins:
        # hmmmm i'm not sure about this try/except blocks but i didnt find
        # anything better for now
        try:
            qty_harmonic = tempo_bin_count[(tempo, "harmonic")]
        except KeyError:
            qty_harmonic = 0

        try:
            qty_percussive = tempo_bin_count[(tempo, "percussive")]
        except KeyError:
            qty_percussive = 0

        if qty_harmonic >= n_harmonic and qty_percussive >= n_percussive:
            possible_tempo.append(tempo)

    return possible_tempo


def time_stretch(stems, base_tempo, duration):
    r"""
    Receive a base_tempo and stretch select stems to match it.

    Parameters
    ----------
    stems : list[dict]
    base_tempo : float

    Returns
    -------
    stems
    """

    for s in stems:
        stem_tempo = s["tempo"]

        audio_path = os.path.join(s["data_home"], s["stem_name"])
        # removing silences at beginning and ending
        audio, sr = librosa.load(audio_path, sr=DEFAULT_SR, duration=duration * 2)
        audio, _ = librosa.effects.trim(audio)

        new_tempo = base_tempo / stem_tempo
        s["stretched_audio"] = librosa.effects.time_stretch(audio, rate=new_tempo)

    return stems


def align_first_beat(stems):
    r"""
    Zero pad stems so their first beat is aligned.

    Parameters
    ----------
    stems : list(dict)
        stems with their respective metadata

    Returns
    -------
    aligned_stems : list(dict)
        stems with audio correct
    """

    aligned_stems = stems.copy()

    latest_beat_time = 0

    for s in aligned_stems:
        _, beat_frames = librosa.beat.beat_track(y=s["stretched_audio"], sr=DEFAULT_SR)
        beat_times = librosa.frames_to_time(beat_frames, sr=DEFAULT_SR)
        s["first_beat_time"] = beat_times[0]

        if s["first_beat_time"] > latest_beat_time:
            latest_beat_time = s["first_beat_time"]

    for s in aligned_stems:
        shift_difference = np.abs(s["first_beat_time"] - latest_beat_time)
        silence_samples = int(shift_difference * DEFAULT_SR)
        s["audio"] = np.pad(
            s["stretched_audio"],
            (silence_samples, 0),
            "constant",
            constant_values=(0, 0),
        )

    return aligned_stems


def mix(duration, stems, strategy="zeros"):
    r"""
    Receives final processed
    audios and cuts them all to the length of the shortest audio to ensure there will be no
    silence. Creates a list of the truncated stems and cuts them again to fit desired duration>
    Then adds stems together to create mixture and also writes off each stem as a sound file to
    uuid output folder. This writing process ONLY occurs if mixture is valid, final check in place.

    Parameters
    ----------
    duration : float
        desired duraiton
    stems : list[dict]
        list with stems we're combining
    strategy : str
        strategy to deal with stems shorter than desired mixture duration.
        * zeros: add silence to the end of the stem (default)
        * cut: cut all stems to minimum lenght
        * repeat: repeat stem and cut it to match mixture duration

    Returns
    ----------
    None
    """

    mixture_length = int(duration * DEFAULT_SR)
    mixture_audio = np.zeros(mixture_length)

    # TODO: implement strategies
    for s in stems:
        # pad ending with zeros
        s["audio"] = librosa.util.fix_length(data=s["audio"], size=mixture_length)
        mixture_audio += librosa.util.normalize(s["audio"])

    return mixture_audio, stems


def generate_mixtures(
    data_home,
    n_mixtures,
    n_stems,
    n_harmonic,
    n_percussive,
    duration,
    index_file="index.csv",
    output_folder="mixtures",
):
    """
    Main method to generate mixtures

    Parameters
    ----------
    data_home : str
        path to stems
    n_mixtures : int
        number of mixtures
    n_stems : int
        number of stems per mixture
    n_harmonic : int
        number of harmonic stems
    n_percussive : int
        number of percussive stems
    duration : float
        mixture duration

    Returns
    -------
    None
    """

    stems, base_tempo = select_stems(n_percussive, n_harmonic, data_home,
            index_file, base_stem=None)
    stems = time_stretch(stems, base_tempo, duration)
    stems = align_first_beat(stems)
    mixture, stems = mix(duration, stems)
    save_mixture(output_folder, mixture, stems)

    return


def save_mixture(output_folder, mixture, stems):
    """
    write mixture to .wav file and metadata to .json file

    Parameters
    ----------
    output_folder : str
        path to folder where we will save mixtures
    mixture : np.array
        mixture audio
    stems : dict
        dictionary with metadata about the stems used to create the mixture

    Returns
    -------
    None
    """
    os.makedirs(output_folder, exist_ok=True)
    mixture_id = str(uuid.uuid4())
    mixture_path = os.path.join(output_folder, mixture_id)

    sf.write(f"{mixture_path}.wav", mixture, DEFAULT_SR)

    for s in stems:
        s.pop("stretched_audio", None)
        s.pop("audio", None)

    with open(f"{mixture_path}.json", "w") as f:
        json.dump(stems, f)

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="mix.py", description="Generating mixtures")

    parser.add_argument(
        "--data_home", required=True, help="pathway to where is data is stored"
    )
    parser.add_argument(
        "--output_folder",
        required=False,
        default="mixtures",
        help="folder where to save the mixtures.",
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        required=False,
        help="set mixture duration. default is 5 seconds",
    )

    parser.add_argument(
        "--n_mixtures",
        required=False,
        default=5,
        help="number of mixtures created",
        type=int,
    )
    parser.add_argument(
        "--n_stems",
        required=False,
        default=3,
        help="number of stems pertaining to each mix",
        type=int,
    )
    parser.add_argument(
        "--n_harmonic",
        required=False,
        default=0,
        help="number of harmonic stems",
        type=int,
    )
    parser.add_argument(
        "--n_percussive",
        required=False,
        default=0,
        help="number of percussive stems",
        type=int,
    )
    parser.add_argument(
        "--index_file",
        required=False,
        default="index.csv",
        help="index file with pre-computed features",
        type=str,
    )

    args = parser.parse_args()

    if args.n_harmonic + args.n_percussive != args.n_stems:
        args.n_harmonic = args.n_stems // 2
        args.n_percussive = args.n_stems - args.n_harmonic

    pbar = tqdm.tqdm(range(args.n_mixtures))
    pbar.set_description("Generating mixtures")
    kwargs = vars(args)

    for i in pbar:
        # each mixture has its own arguments
        mixture_args = kwargs.copy()
        generate_mixtures(**mixture_args)
