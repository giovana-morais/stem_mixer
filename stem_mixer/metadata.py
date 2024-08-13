#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. autosummary::
   :toctree: generated/

   dict_template
   feature_extraction
   check_file_number
   save_stem_dataframe
   brid_track_info
   musdb_track_info
"""
import argparse
import glob
import json
import os

import pandas as pd
import tqdm

from stem_mixer import features

DEFAULT_SR = 44100
BRID_INDEX = "brid_index.txt"
MUSDB_INDEX = "musdb_index.txt"


def dict_template(data_home=None, stem_name=None):
    r"""
    Create empty metadata dictionary

    Parameters
    ----------
    data_home : str or None
    stem_name : str or None

    Returns
    -------
    metadata : dict
        dictionary with empty metadata
    """

    metadata = {
        "stem_name": stem_name,
        "data_home": data_home,
        "tempo": None,
        "key": None,
        "sound_class": None,
    }

    return metadata


def feature_extraction(stem_path, track_metadata=None, overwrite=False):
    r"""
    Takes file path to a stem, calculate features and save the metadata as JSON.

    Parameters
    ----------
    stem_path: str
        Path to the audio stem file.
    metadata: dict (optional)
        dictionary with pre-computed metadata
    overwrite: boolean
        if True, overwrite a JSON file that already exists

    Returns
    -------
    None
    """

    json_file_path = os.path.splitext(stem_path)[0] + ".json"

    if track_metadata is None:
        track_metadata = dict_template()

    if not os.path.exists(json_file_path) or overwrite:
        metadata = track_metadata.copy()

        if metadata["tempo"] is None:
            metadata["tempo"] = features.tempo(stem_path)

        if metadata["sound_class"] is None:
            metadata["sound_class"] = features.sound_class(stem_path)

        metadata["tempo_bin"] = features.tempo_bin(metadata["tempo"])

        with open(json_file_path, "w") as json_file:
            json.dump(metadata, json_file, indent=4)

    return


def check_file_number(json_files, wav_files):
    if len(json_files) < len(wav_files):
        diff = len(wav_files) - len(json_files)
        preprocess = input(
            f"Number of files do not match! {diff} files need to be processed in order to be used. Do you want to process it right now? [y/N]"
        )

        if preprocess == "y":
            print("Preprocessing...")
        else:
            print("Ok, moving on without those tracks!")
    return


def save_stem_dataframe(data_home, index_file="index.csv"):
    json_files = glob.glob(os.path.join(data_home, "*.json"))
    wav_files = glob.glob(os.path.join(data_home, "*.wav"))

    data = []
    # check_file_number(json_files, wav_files)
    for file in json_files:
        with open(file, "r") as f:
            data.append(json.load(f))  # extracting json data
        # print(f)

    df = pd.DataFrame.from_dict(data)
    df.to_csv(os.path.join(data_home, index_file), index=False)

    return df


def brid_track_info(data_home, tid):
    r"""
    BRID DATASET PRE-PROCESSING

    Takes file path to BRID stem and assigns instrument variable based on file name

    Parameters
    ----------
    data_home : str
        folder containing stems
    tid : str
        track id

    Returns
    -------
    tempo : float
        tempo of stem based on style
    instrument_name : str
        name of BRID instrument if exists
    key : None
    sound_class : str
        sound_class of BRID stem, "percussive"
    """

    track_metadata = dict_template()
    track_metadata["stem_name"] = tid
    track_metadata["data_home"] = data_home
    track_metadata["key"] = None
    track_metadata["sound_class"] = "percussive"

    suffix_to_instr = {
        "PD": "pandeiro",
        "TB": "tamborim",
        "RR": "reco-reco",
        "CX": "caixa",
        "RP": "repique",
        "CU": "cuica",
        "AG": "agogo",
        "SK": "shaker",
        "TT": "tanta",
        "SU": "surdo",
    }

    suffix_to_tempo = {
        "SA.wav": 80.0,
        "PA.wav": 100.0,
        "CA.wav": 65.0,
        "SE.wav": 130.0,
        "MA.wav": 120.0,
    }

    # BRID stems adhere to the following structure: [GID#] MX-YY-ZZ.wav
    suffix_list = tid.split("-")

    # drop the number that refers to instrumentalist
    instr_suffix = suffix_list[1][0:2]
    track_metadata["instrument_name"] = suffix_to_instr.get(instr_suffix, None)

    style_suffix = suffix_list[-1]
    track_metadata["tempo"] = suffix_to_tempo.get(style_suffix, None)

    return track_metadata


def musdb(data_home):
    """
    create metadata for MUSDB tracks present in `data_home`.
    """
    musdb_stems = stems_from_file(MUSDB_INDEX)

    all_stems = [
        os.path.basename(tid) for tid in glob.glob(os.path.join(data_home, "*.wav"))
    ]
    all_stems = set(all_stems)

    # process only what we have inside the stems folder
    available_stems = all_stems.intersection(musdb_stems)

    pbar = tqdm.tqdm(available_stems)
    pbar.set_description("Processing MUSDB stems")

    for tid in pbar:
        track_metadata = musdb_track_info(data_home, tid)
        feature_extraction(os.path.join(data_home, tid), track_metadata)

    return


def musdb_track_info(data_home, tid):
    r"""
    MUSDB DATASET PRE-PROCESSING

    Takes file path to MUSDB stem and assigns variables based on file name

    Note: to make use of this function, save MUSDB stems as
        "artist - track_title - stem_type.wav"
    where stem_title is "vocals", "drums", "bass", or "other"

    i.e. "Bobby Nobody - Stich Up - drums.wav"

    Parameters
    ----------
    data_home : str
        path to folder containing stems
    tid: str
        track id

    Returns
    -------
    tempo : None
    instrument_name : str
        name of MUSDB instrument / type if exists
    key : None
    sound_class : str
        sound class of stem if instrument_name exists and is "vocals", "drums", "bass", or "other"
    """
    track_metadata = dict_template(data_home=data_home, stem_name=tid)

    stem_name = tid.split("-")[-1].strip()
    # removing .wav extension
    stem_name = os.path.splitext(stem_name)[0]

    track_metadata["instrument_name"] = stem_name if stem_name != "other" else None

    sound_class = None
    if stem_name == "vocals":
        sound_class = "vocals"
    elif stem_name == "drums":
        sound_class = "percussive"
    elif stem_name == "bass" or stem_name == "other":
        sound_class = "harmonic"

    track_metadata["sound_class"] = sound_class

    return track_metadata


def brid(data_home):
    r"""
    create metadata for BRID tracks present in `data_home`.
    """
    brid_stems = stems_from_file(BRID_INDEX)

    all_stems = [
        os.path.basename(tid) for tid in glob.glob(os.path.join(data_home, "*.wav"))
    ]
    all_stems = set(all_stems)

    # process only what we have inside the stems folder
    available_stems = all_stems.intersection(brid_stems)

    pbar = tqdm.tqdm(available_stems)
    pbar.set_description("Processing BRID stems")

    for tid in pbar:
        track_metadata = brid_track_info(data_home, tid)
        feature_extraction(os.path.join(data_home, tid), track_metadata)

    return


def stems_from_file(filename):
    r"""
    return a list of stems from a txt file
    """

    index_path = os.path.join(os.path.dirname(__file__), filename)

    with open(index_path, "r") as f:
        stems = f.read().splitlines()

    return stems


def process(data_home, datasets=None):
    r"""
    generate metadata for all stems in the folder

    Parameters
    ----------
    data_home : str
        path to folder with stems
    dataset : list
        if dataset is provided, we process their respective tracks first
        using the specific information we know, such as instruments and
        tempo.
        supported datasets are ["brid", "musdb"]

    Returns
    -------
    None
    """
    # create a set with all stems (basename only)
    available_stems = set(
        [os.path.basename(tid) for tid in glob.glob(os.path.join(data_home, "*.wav"))]
    )

    all_stems = available_stems.copy()

    if datasets is not None and "brid" in datasets:
        # process tracks
        brid(data_home)
        # update stems list so we don't reprocess a brid stem
        brid_stems = set(stems_from_file(BRID_INDEX))
        available_stems = available_stems.difference(brid_stems)

    if datasets is not None and "musdb" in datasets:
        # process tracks
        musdb_stems = set(stems_from_file(MUSDB_INDEX))
        # update stems list so we don't reprocess a musdb stem
        musdb(data_home)
        available_stems = available_stems.difference(musdb_stems)

    # process remaining stems
    pbar = tqdm.tqdm(available_stems)
    pbar.set_description("Processing remaining stems")
    for tid in pbar:
        track_metadata = dict_template(data_home, tid)
        feature_extraction(os.path.join(data_home, tid), track_metadata=track_metadata)

    print("Writing stems dataframe")
    save_stem_dataframe(data_home, index_file="index.csv")
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="PreprocessingHelper",
        description="This script creates metadata for BRID and/or MUSDB",
    )

    parser.add_argument(
        "--data_home", required=True, help="pathway to where is data is stored"
    )
    parser.add_argument(
        "--datasets",
        required=False,
        help="supported datasets: BRID (enter 'brid') and MUSDB (enter 'musdb')",
    )

    args = parser.parse_args()

    if args.datasets is not None:
        args.datasets = args.datasets.split(",")

    process(args.data_home, args.datasets)
