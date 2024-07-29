import argparse
import os
import glob
import json
import random
import uuid

import librosa
import numpy as np
import soundfile as sf

DEFAULT_SR = 44100

def organize_files(data_home, n_stems, n_harmonic, n_percussive):

    """

    Organizes json files based on whether they pertain to harmonic or percussive sound classes.
     --> More specifically, creates dictionary for each "tempo bin" so we can find groups of 
         harmonic and percussive stems of similar tempos very easily
     --> In dictionary, essential metadata is alos stored for mixture making

    Checks input values for n_harmonic and n_percussive.
     --> If they are not given, OR if they are provided incorrectly, they are re-defined as 
         values that won't break

    Parameters
    ----------

    data_home(str): path to stems
    n_stems(int): number of stems to make up the mixture
    n_harmonic(int): number of harmonic stems
    n_percussive(int): number of percussive stems

    Returns
    --------

    n_harmonic(int): number of harmonic stems (same as input if no changes needed to be applied)
    n_percussive(int): number of percussive stems (same as input if no changes needed to be applied)
    tempo_bin_harmonic(dict): dictionary to store tempo groupings of harmonic stems w/ metadata
    tempo_bin_percussive(dict): dictionary to store tempo groupings of percussive stems w/ metadata
    """



    # first check to make sure user has not provided n_harm and n_perc such that n_harm + n_perc != n_total
    if n_harmonic + n_percussive != n_stems:
        n_harmonic = n_stems // 2
        n_percussive = n_stems - n_harmonic


    json_files = glob.glob(os.path.join(data_home, "*.json"))

    tempo_bin_harmonic = {}
    tempo_bin_percussive = {}


    for file in json_files: # splitting jsons into harmonic and percussive
        # i did this because when it comes to picking stems, this is first thing to consider

        with open(file, "r") as f:
            split_name = os.path.basename(file)
            stem_name, _ = os.path.splitext(split_name)

            data = json.load(f) # extracting json data

            tempo_bin = data.get("tempo_bin")
            original_tempo = data.get("tempo")
            instrument_name = data.get("instrument_name")
            key = data.get("key")

            if data.get("sound_class") == "percussive": # splitting into harmonic and percussive

                if tempo_bin not in tempo_bin_percussive:
                    tempo_bin_percussive[tempo_bin] = {} # initializing a dictionary for each new tempo bin

                tempo_bin_percussive[tempo_bin][stem_name] = {
                        "original tempo" : original_tempo,
                        "instrument" : instrument_name,
                        "key" : key
                        } # necessary metadata


            elif data.get("sound_class") == "harmonic":

                if tempo_bin not in tempo_bin_harmonic:
                    tempo_bin_harmonic[tempo_bin] = {}

                tempo_bin_harmonic[tempo_bin][stem_name] = {
                        "original tempo" : original_tempo,
                        "instrument" : instrument_name,
                        "key" : key
                        }

    print("tempo bin harmonic ", tempo_bin_harmonic[100])
    print("tempo bin percussive ", tempo_bin_percussive)


    return n_harmonic, n_percussive, tempo_bin_harmonic, tempo_bin_percussive

def select_tracks(data_home, n_stems, n_harmonic, n_percussive, tempo_bin_harmonic, tempo_bin_percussive):

    """

    Selects n_stems number of tracks under random tempo threshold to create a mixture while
    implementing checks along the way to ensure that the validity of the mixture before moving 
    on to next step. i.e.

    - Checks that there is a base tempo and that a tempo bin exists for it
    - Checks that there is no instrument repetition when this field is known
    - Checks that number of selected stems equals number of desired stems
    - Checks against any additional unexpected errors

    Parameters
    ----------

    data_home(str): path to stems
    n_stems(int): number of stems to make mixture
    n_harmonic(int): number of harmonic stems
    n_percussive(int): number of percussive stems
    tempo_bin_harmonic(dict): dictionary of tempo groupings and metadata for harmonic stems
    tempo_bin_percussive(dict): dictionary of tempo groupings and metadata for percussive stems

    Returns
    -------

    selected_stems(dict): stem tracks to make mixture w/ relevant metadata
    base_tempo(int): tempo that all stems will adhere to in next step
    invalid_mixture(bool): a check to see if mixture is still valid

    """

    # taking invalid mixture as parameter, initialized as False with each iteration and passed as parameter

    # initialization outside of try block
    invalid_mixture = False
    selected_stems = {}
    base_tempo = 0

    try:

        if n_percussive > 0:
            # want base tempo to be percussive stem unless user wants mix to be all harmonic
            # selects random key from dictionary constructed in organize_files
            base_tempo = random.sample(list(tempo_bin_percussive.keys()), 1)[0] 

        else:
            # resorts to harmonic if no percussive
            base_tempo = random.sample(list(tempo_bin_harmonic.keys()), 1)[0]

        print("base tempo ", base_tempo)

        for i in range(0, n_percussive): # adding n_percussive amount of percussive stems to mix

            if tempo_bin_percussive.get(base_tempo) is not None:

                # extracting stem
                percussive_stem = random.sample(list(tempo_bin_percussive.get(base_tempo).keys()), 1)[0]

                # extracting other relevant metadata
                instrument = tempo_bin_percussive.get(base_tempo).get(percussive_stem).get("instrument")
                original_tempo = tempo_bin_percussive.get(base_tempo).get(percussive_stem).get("original tempo")
                key = tempo_bin_percussive.get(base_tempo).get(percussive_stem).get("key")

                selected_stems[percussive_stem] = [original_tempo, instrument, key] # appending stem with its metadata

            else:
                invalid_mixture = True # mixture is not valid if tempo bin is None 
                print("invalid, None base tempo")

        for i in range(0, n_harmonic):

            if tempo_bin_harmonic.get(base_tempo) is not None:

                # extracting stem
                harmonic_stem = random.sample(list(tempo_bin_harmonic.get(base_tempo).keys()), 1)[0]

                # extracting other relevant metadata
                instrument = tempo_bin_harmonic.get(base_tempo).get(harmonic_stem).get("instrument")
                original_tempo = tempo_bin_harmonic.get(base_tempo).get(harmonic_stem).get("original tempo")
                key = tempo_bin_harmonic.get(base_tempo).get(harmonic_stem).get("key")

                selected_stems[harmonic_stem] = [original_tempo, instrument, key] # adding harmonic stems + metadata

            else:
                invalid_mixture = True
                print("invalid, tempo bin DNE")

        list_of_instruments = []
        for stem in selected_stems.keys():
            instrument = selected_stems.get(stem)[1]
            list_of_instruments.append(instrument) # want to check to see what instruments were selected

        # want list of instruments with *NO None VALUES* to make sure no repition where there are instruments filled in
        # we cannot control when instruments are None so we need to filter these cases out and only check what we can control
        filtered_instruments = [instr for instr in list_of_instruments if instr is not None]
        if len(filtered_instruments) != len(set(filtered_instruments)): # checking for repeated instruments
            invalid_mixture = True # if instruments repeat, invalid mixture
            print("invalid, instrument repetition")

        if len(selected_stems) != n_stems: # if, for some reason, selected stems less than number of stems, invalid mixture
            invalid_mixture = True
            print("invalid, cant fill desired number of stems")

    except ValueError: # if any error gets thrown, invalid mixture
        invalid_mixture = True
        print("invalid, unexpected error")

    print("selected stems: ", selected_stems)

    return selected_stems, base_tempo, invalid_mixture

def stretch(data_home, n_stems, selected_stems, base_tempo):

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

    stretched_audios(list): list of stretched audios
    invalid_mixture(bool): check of mixture validity
    """

    invalid_mixture = False

    audio_files = glob.glob(os.path.join(data_home, "*.wav")) + glob.glob(os.path.join(data_home, "*.mp3"))
    stretched_audios = []
    selected_stems_keys = list(selected_stems.keys())

    #if invalid_mixture == False:
    target_tempo = base_tempo
    print("target tempo", target_tempo)

    for i in range(0, n_stems):
        stem_to_stretch = selected_stems_keys[i]
        current_tempo = selected_stems[stem_to_stretch][0] # extracting tempo from dict
        print("current tempo", current_tempo)

        for file in audio_files: # is there a way to make this more efficient?
            if stem_to_stretch in file:
                print("audio file found: ", stem_to_stretch)
                wav_file = file

        audio, sr = librosa.load(wav_file, sr=DEFAULT_SR)
        audio_norm = librosa.util.normalize(audio)

        audio, sr = librosa.load(wav_file, sr=sr)
        audio_norm = librosa.util.normalize(audio)

        new_rate = float(target_tempo / current_tempo)
        stretched_audio = librosa.effects.time_stretch(audio_norm, rate=new_rate)

        stretched_audios.append(stretched_audio)

    if len(stretched_audios) != n_stems:
        invalid_mixture = True
        print("invalid, we lost a stretched audio")

    return stretched_audios, invalid_mixture

def shift(stretched_audios):

    """

    Receives audios post-stretching and collects information on their first downbeats and stores as
    a list. It then finds the index of the audio of the latest downbeat and holds that audio
    constant while shifting every other audio by the difference between their first downbeat
    and the latest-occurring first downbeat by padding audiofile with zeroes. It then double checks
    first-downbeats to make sure that they are all the same. 

    Parameters
    ----------

    stretched_audios(list): list of stretched audios

    Returns
    -------
    final_audios(list): list of shifted audios
    invalid_mixture(bool): check of mixture validity

    """


    first_downbeats = []
    final_audios = []
    invalid_mixture = False

    try:

        for audio in stretched_audios:
            _, beat_times = librosa.beat.beat_track(y=audio, sr=DEFAULT_SR)
            downbeat_times = librosa.frames_to_time(beat_times, sr=DEFAULT_SR)
            first_downbeats.append(downbeat_times[0])

        latest_beat = max(first_downbeats)
        latest_beat_index = first_downbeats.index(latest_beat)

        fixed_audio = stretched_audios[latest_beat_index]

        final_audios.append(fixed_audio)

        for i in range(0, len(stretched_audios)):
            if i != latest_beat_index:
                shift_difference = np.abs(first_downbeats[i] - latest_beat)
                silence_samples = int(shift_difference * DEFAULT_SR)
                silence = np.zeros(silence_samples)

                final_audio = np.concatenate([silence, stretched_audios[i]])


                # rechecking downbeats after shift
                print("rechecking downbeat alignment")
                _, beat_times = librosa.beat.beat_track(y=final_audio, sr=DEFAULT_SR)
                downbeat_times = librosa.frames_to_time(beat_times, sr=DEFAULT_SR)
                print(downbeat_times[0])

                final_audios.append(final_audio)
    except:
        invalid_mixture=True

    return final_audios, invalid_mixture

def concatenate(data_home, duration, final_audios):

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
    os.makedirs(mixture_folder, exist_ok = True)

    final_audios_lengths = []
    for stem in final_audios:
        final_audios_lengths.append(len(stem))

    min_length = min(final_audios_lengths)

    if min_length < duration:
        invalid_mixture = True # checking min length against duration

    total_length = min_length
    start_sample = max(0, total_length - int(duration*DEFAULT_SR))
    end_sample = total_length

    truncated_stems = []
    for audio in final_audios:

        audio = audio[:min_length]
        audio = audio[start_sample:end_sample]
        truncated_stems.append(audio)

    length = len(truncated_stems[0])
    mixture_audio = np.zeros(length) # initialization

    for stem in truncated_stems:
        if len(stem) == 0:
            invalid_mixture = True
            print("invalid, empty stem")
        mixture_audio += stem

    if not invalid_mixture: # if it passes all checks

        mixture_id = str(uuid.uuid4())
        individual_output_folder = os.path.join(mixture_folder, mixture_id)
        os.makedirs(individual_output_folder, exist_ok=True)


        for k in range(0, len(truncated_stems)):
            sf.write(f"{individual_output_folder}/stem{k+1}.wav", truncated_stems[k], DEFAULT_SR)


        sf.write(f"{individual_output_folder}/mixture.wav", mixture_audio, DEFAULT_SR)


def generate_mixtures(data_home, n_mixtures, n_stems, n_harmonic, n_percussive, duration):

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


    n_harmonic, n_percussive, tempo_bin_harmonic, tempo_bin_percussive = organize_files(data_home, n_stems, n_harmonic, n_percussive)

    count = 0
    while count < n_mixtures:


        print("")
        print("trying to fetch a mixture")

        selected_stems, base_tempo, invalid_mixture = select_tracks(data_home, n_stems, n_harmonic, n_percussive, tempo_bin_harmonic, tempo_bin_percussive)
        if invalid_mixture:
            print("invalid")
            continue
        stretched_audios, invalid_mixture = stretch(data_home, n_stems, selected_stems, base_tempo)
        if invalid_mixture:
            print("invalid")
            continue
        final_audios, invalid_mixture = shift(stretched_audios)
        if invalid_mixture:
            print("invalid")
            continue

        concatenate(data_home, duration, final_audios)

        print("sending valid mixture to folder ...\n")

        count += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="StemMixer", description="Generating mixtures"
    )
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
        "--n_mixtures", required=False, default=5, help="number of mixtures created",
        type=int
    )
    parser.add_argument(
        "--n_stems",
        required=False,
        default=3,
        help="number of stems pertaining to each mix",
        type=int
    )
    parser.add_argument(
        "--n_harmonic", required=False, default=0, help="number of harmonic stems", 
        type=int
    )
    parser.add_argument(
        "--n_percussive", required=False, default=0, help="number of percussive stems", 
        type=int
    )

    args = parser.parse_args()
    kwargs = vars(args)


    generate_mixtures(
        args.data_home,
        args.n_mixtures,
        args.n_stems,
        args.n_harmonic,
        args.n_percussive,
        args.duration
    )

