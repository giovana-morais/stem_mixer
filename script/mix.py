import argparse
import os
import glob
import json
import random
import uuid

import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import tqdm

DEFAULT_SR = 44100
# MAX_TRIES = 10

def select_stems(base_stem=None, **kwargs):
    """
    select stems from the index

    arguments
    ---
        base_stem : str
        **kwargs : dict
            additional arguments

    return
    ---
        stems : list[dict]
            list with stems that will be used for mixture
            each element of the list is a dictionary with the necessary
            information about that stem.
        base_tempo : int
            tempo_bin from the base stem
    """

    index = pd.read_csv(os.path.join(kwargs["data_home"], kwargs["index_file"]))

    # base_stem for now is random if not provided
    if base_stem is not None:
        base_stem = index[index["stem_name"] == base_stem]
    elif kwargs["n_percussive"] > 0:
        base_stem = index[index["sound_class"] == "percussive"].sample()
    else:
        base_stem = index[index["sound_class"] == "harmonic"].sample()

    base_stem = base_stem.to_dict("records")[0]

    # update n_percussives/n_harmonics
    # @lindsey: what if base_stem is undetermined?
    if base_stem["sound_class"] == "percussive":
        kwargs["n_percussive"] -= 1
    elif base_stem["sound_class"] == "harmonic":
        kwargs["n_harmonic"] -= 1

    base_tempo = base_stem["tempo_bin"]

    # TODO: remove base stem from index
    # here is where we can also add tempo octaves
    index_filtered = index[
            (index["tempo_bin"] == base_stem["tempo_bin"])
            & (index["instrument_name"] != base_stem["instrument_name"])
        ]

    # TODO: add instrument checking
    # sample percussive
    percussive = []
    if kwargs["n_percussive"] > 0:
        percussive = index_filtered.sample(kwargs["n_percussive"]).to_dict("records")

    # sample harmonic
    harmonic = []
    if kwargs["n_harmonic"] > 0:
        harmonic = index_filtered.sample(kwargs["n_harmonic"]).to_dict("records")

    stems = [base_stem] + percussive + harmonic

    return stems, base_tempo


def time_stretch(stems, base_tempo):
    """
    Receives base tempo and selected stem dictionary with metadata related to their original tempo,
    instrument, and key. Then stretches stems to be the same tempo as base tempo. Also implements
    checks of mixture validity.

    Parameters
    ---------
        data_home(str): path to data home
        n_stems(int): number of stems in output mixture
        selected_stems(dict): stem names with respective metadata to be stretched
        base_tempo(int): tempo all stems will be adjusted to

    Returns
    -------
        stems
    """

    for s in stems:
        stem_tempo = s["tempo"]

        audio_path = os.path.join(s["data_home"], s["stem_name"])
        audio, sr = librosa.load(audio_path, sr=DEFAULT_SR)

        new_tempo = base_tempo/stem_tempo
        s["stretched_audio"] = librosa.effects.time_stretch(audio, rate=new_tempo)

    return stems


def align_stems(stems):
    """
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
        silence = np.zeros(silence_samples)

        s["stem_audio"] = np.pad(s["stretched_audio"], (silence_samples, 0), "constant", constant_values=(0,0))

    return aligned_stems


def mix(data_home, duration, stems):
    """
    Creates output folder for mixtures if it does not already exist. Receives final processed
    audios and cuts them all to the length of the shortest audio to ensure there will be no
    silence. Creates a list of the truncated stems and cuts them again to fit desired duration>
    Then adds stems together to create mixture and also writes off each stem as a sound file to
    uuid output folder. This writing process ONLY occurs if mixture is valid, final check in place.

    Parameters
    ----------

    data_home(str): path to stems
    duration(float): desired duraiton
    final_audios(list): stretched and padded audios

    Returns
    ________

    None

    """

    invalid_mixture = False

    mixture_folder = os.path.join(data_home, "..", "mixtures")
    os.makedirs(mixture_folder, exist_ok=True)

    final_audios_lengths = []
    for stem in final_audios:
        final_audios_lengths.append(len(stem))

    min_length = min(final_audios_lengths)

    if min_length < duration:
        invalid_mixture = True  # checking min length against duration

    total_length = min_length
    start_sample = max(0, total_length - int(duration * DEFAULT_SR))
    end_sample = total_length

    truncated_stems = []
    for audio in final_audios:
        audio = audio[:min_length]
        audio = audio[start_sample:end_sample]
        truncated_stems.append(audio)

    length = len(truncated_stems[0])
    mixture_audio = np.zeros(length)  # initialization

    for stem in truncated_stems:
        if len(stem) == 0:
            invalid_mixture = True
            print("invalid, empty stem")
        mixture_audio += stem

    if not invalid_mixture:  # if it passes all checks
        mixture_id = str(uuid.uuid4())
        individual_output_folder = os.path.join(mixture_folder, mixture_id)
        os.makedirs(individual_output_folder, exist_ok=True)

        for k in range(0, len(truncated_stems)):
            sf.write(
                f"{individual_output_folder}/stem{k+1}.wav",
                truncated_stems[k],
                DEFAULT_SR,
            )

        sf.write(f"{individual_output_folder}/mixture.wav", mixture_audio, DEFAULT_SR)


def generate_mixtures(**kwargs):
    """
    Consolidates whole mixture-making process under one function call. Between each step checks
    to see if mixture is still valid, reruns if not. Runs until desired number of mixtures are
    created.

    Parameters
    ----------
    data_home(str): path to stems
    n_mixtures(int): number of mixtures
    n_stems(int): number of stems per mixture
    n_harmonic(int): number of harmonic stems
    n_percussive(int): number of percussive stems
    duration(float): mixture duration

    Returns
    -------

    None
    """

    count = 0
    # max_tries = 0
    while count < kwargs["n_mixtures"]: # or max_tries < MAX_TRIES:
        print("trying to fetch a mixture")

        stems, base_tempo = select_stems(**kwargs)
        stems = time_stretch(stems, base_tempo)
        stems = align_stems(stems)
        mix(data_home, duration, final_audios)

        # print("sending valid mixture to folder ...\n")

        count += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="mix.py", description="Generating mixtures")

    parser.add_argument(
        "--data_home", required=True, help="pathway to where is data is stored"
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
