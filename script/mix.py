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

def select_stems(n_percussive, n_harmonic, data_home, index_file, base_stem=None, **kwargs):
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

    index = pd.read_csv(os.path.join(data_home, index_file))

    # base_stem for now is random if not provided
    if base_stem is not None:
        base_stem = index[index["stem_name"] == base_stem]
    elif n_percussive > 0:
        base_stem = index[index["sound_class"] == "percussive"].sample()
    else:
        base_stem = index[index["sound_class"] == "harmonic"].sample()

    index.drop(base_stem.index, inplace=True)

    base_stem = base_stem.to_dict("records")[0]
    print(f"TEMPO BIN: {base_stem['tempo_bin']}")

    # update n_percussives/n_harmonics
    # @lindsey: what if base_stem is undetermined?
    if base_stem["sound_class"] == "percussive":
        n_percussive -= 1
    elif base_stem["sound_class"] == "harmonic":
        n_harmonic -= 1

    base_tempo = base_stem["tempo_bin"]

    # here is where we can also add tempo octaves
    index_filtered = index[
            (index["tempo_bin"] == base_stem["tempo_bin"])
            & (index["instrument_name"] != base_stem["instrument_name"])
        ]

    # TODO: add instrument checking

    # sample percussive
    percussive = []
    if n_percussive > 0:
        percussive_index = index_filtered[index_filtered["sound_class"] == "percussive"]
        if len(percussive_index) < n_percussive:
            raise ValueError("Number of requested percussive stems is smaller than stems available in this tempo_bin")

        percussive = percussive_index.sample(n_percussive).to_dict("records")

    # sample harmonic
    harmonic = []
    if n_harmonic > 0:
        harmonic_index = index_filtered[index_filtered["sound_class"] == "harmonic"]
        if len(harmonic_index) < n_harmonic:
            raise ValueError("Number of requested harmonic stems is smaller than stems available in this tempo_bin")

        harmonic = harmonic_index.sample(n_harmonic).to_dict("records")
        print(len(harmonic))

    stems = [base_stem] + percussive + harmonic

    # print(stems)
    print(f"we want {n_harmonic + n_percussive + 1} stems")
    print(f"we got {len(stems)} stems")

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

        s["audio"] = np.pad(s["stretched_audio"], (silence_samples, 0), "constant", constant_values=(0,0))

    return aligned_stems


def mix(duration, stems, strategy="cut"):
    """
    Receives final processed
    audios and cuts them all to the length of the shortest audio to ensure there will be no
    silence. Creates a list of the truncated stems and cuts them again to fit desired duration>
    Then adds stems together to create mixture and also writes off each stem as a sound file to
    uuid output folder. This writing process ONLY occurs if mixture is valid, final check in place.

    Parameters
    ----------

    data_home(str): path to stems
    duration(float): desired duraiton
    final_audios(list): stretched and padded audios
    strategy : str
        strategy to deal with stems shorter than desired mixture duration.
        * zeros: add silence to the end of the stem (default)
        * cut: cut all stems to minimum lenght
        * repeat: repeat stem and cut it to match mixture duration

    Returns
    ________

    None

    """

    for s in stems:
        s["audio"] = librosa.util.fix_length(data=s["audio"], size=int(duration*DEFAULT_SR))

    # final_audios_lengths = []
    # for stem in final_audios:
    #     final_audios_lengths.append(len(stem))

    # min_length = min(final_audios_lengths)

    # if min_length < duration:
    #     invalid_mixture = True  # checking min length against duration

    # total_length = min_length
    # start_sample = max(0, total_length - int(duration * DEFAULT_SR))
    # end_sample = total_length

    # truncated_stems = []
    # for audio in final_audios:
    #     audio = audio[:min_length]
    #     audio = audio[start_sample:end_sample]
    #     truncated_stems.append(audio)

    # length = len(truncated_stems[0])
    mixture_audio = np.zeros(int(duration*DEFAULT_SR))  # initialization

    for s in stems:
        mixture_audio += librosa.util.normalize(s["audio"])

    return mixture_audio, stems


def generate_mixtures(data_home, n_mixtures, n_stems, n_harmonic, n_percussive,
        duration, index_file, output_folder):
    """
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

    stems, base_tempo = select_stems(**kwargs)
    stems = time_stretch(stems, base_tempo)
    stems = align_stems(stems)
    mixture, stems = mix(duration, stems)
    save_mixture(output_folder, mixture, stems)

    return

def save_mixture(output_folder, mixture, stems):
    """
    write mixture to .wav file and metadata to .json file
    """
    mixture_id = str(uuid.uuid4())
    sf.write(f"{os.path.join(output_folder, mixture_id)}.wav", mixture, DEFAULT_SR)

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

    os.makedirs(args.output_folder, exist_ok=True)

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
