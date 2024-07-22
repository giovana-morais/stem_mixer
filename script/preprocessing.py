import argparse
import json
import os

import metadata

def brid(file_path):
    """
    BRID DATASET PRE-PROCESSING

    Takes file path to BRID stem and assigns instrument variable based on file name

    Parameters:
        file_path (str) : path to stem

    Returns:
        tempo (float) : tempo of stem based on style
        instrument_name (str) : name of BRID instrument if exists
        key : null
        sound_class (str) : sound_class of BRID stem, "percussive"
    """

    key = None
    sound_class = "percussive"

    suffix_list = file_path.split("-")

    suffix_to_instr = {
            "PD" : "pandeiro",
            "TB": "tamborim",
            "RR": "reco-reco",
            "CX": "caixa",
            "RP": "repique",
            "CU": "cuica",
            "AG": "agogo",
            "SK": "shaker",
            "TT": "tanta",
            "SU": "surdo" 
            }

    instr_suffix = suffix_list[1][0:2]
    instrument_name = suffix_to_instr.get(instr_suffix, None)

    suffix_to_tempo = {
        "SA.wav" : 80.0,
        "PA.wav": 100.0,
        "CA.wav": 65.0,
        "SE.wav": 130.0,
        "MA.wav": 120.0
    }

    # from dataset documentation, brid stems adhere to the following structure: [GID#] MX-YY-ZZ.wav
    style_suffix = suffix_list[-1]
    tempo = suffix_to_tempo.get(style_suffix, None)

    return tempo, instrument_name, key, sound_class


def musdb(file_path):
    """
    MUSDB DATASET PRE-PROCESSING

    Takes file path to MUSDB stem and assigns variables based on file name

    Note: to make use of this function, save MUSDB stems as "artist - track_title - stem_title.wav"
    where stem_title is "vocals", "drums", "bass", or "other"

    i.e. "Bobby Nobody - Stich Up - drums.wav"

    Parameters:
        file_path (str) : path to stem

    Returns:
        tempo : null
        instrument_name (str) : name of MUSDB instrument / type if exists
        key : null
        sound_class : sound class of stem if instrument_name exists and is "vocals", "drums", "bass", or "other"
    """

    key = None
    tempo = None
    sound_class = None

    # removing .wav extension
    stem_name = file_path.split("-")[-1].strip()[0:-4]

    instrument_name = stem_name if stem_name != "other" else None

    if stem_name == "vocals":
        sound_class = "vocals"
    elif stem_name == "drums":
        sound_class = "percussive"
    elif stem_name == "bass" or stem_name == "other":
        sound_class = "harmonic"

    return tempo, instrument_name, key, sound_class

def automatic_preprocessing(data_home):

    # determines if a file pertains to a specific dataset
    # creates metadata json for each file

    path_to_brid = os.path.join(args.data_home, "..", "script", "brid.txt")
    path_to_musdb = os.path.join(args.data_home, "..", "script", "musdb.txt")

    with open(path_to_brid, "r") as bridtxt:
        brid_files = "".join(line.strip() for line in bridtxt)

    with open(path_to_musdb, "r") as musdbtxt:
        musdb_files = "".join(line.strip() for line in musdbtxt)

    for root, dirs, files in os.walk(args.data_home):
        for file in files:
            file_path = os.path.join(root, file)

            if file_path.endswith(".wav"):
                stem_name = os.path.splitext(file_path)[0][6:]
                if stem_name in brid_files:
                    args.tempo, args.instrument_name, args.key, args.sound_class = brid(file_path)
                elif stem_name in musdb_files:
                    args.tempo, args.instrument_name, args.key, args.sound_class = musdb(file_path)
                else:
                    args.tempo = None
                    args.instrument_name = None
                    args.key = None
                    args.sound_class = None

                print("we are performing metadata extraction on: ", file_path)

                metadata.extraction(file_path, **kwargs)

def manual_preprocessing(data_home, stem_name, new_tempo, new_instrument_name, new_key, new_sound_class):
    # at this point, assuming json already made
    # set up example call of this

    json_file = stem_name + ".json"
    path_to_json = os.path.join(data_home, json_file)

    metadata = kwargs.copy()

    with open(path_to_json, "r") as json_file:
        metadata = json.load(json_file)

    metadata["tempo"] = new_tempo
    metadata["instrument_name"] = new_instrument_name
    metadata["key"] = new_key
    metadata["sound_class"] = new_sound_class

    with open(path_to_json, "w") as json_file:
        json.dump(metadata, json_file, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog="PreprocessingHelper",
            description="This script creates metadata for BRID and/or MUSDB"
            )

    # arguments. required --> data home, dataset (if using preprocessing)
    parser.add_argument("--data_home", required=True, help="pathway to where is data is stored")

    args = parser.parse_args()
    kwargs = vars(args)

    automatic_preprocessing(args.data_home)
    #manual_preprocessing(args.data_home, "[0119] S1-PD4-05-CA", 123, "test1", "test2", "test3")



