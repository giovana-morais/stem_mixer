import os
import glob
import json
import random
import uuid

import librosa
import numpy as np
import soundfile as sf

DEFAULT_SR = 22050

def precheck(data_home, n_stems, n_harmonic, n_percussive):

    # this only needs to run once
    n_harmonic = int(n_harmonic)
    n_percussive = int(n_percussive)
    n_stems = int(n_stems)

    # first check to make sure user has not provided n_harm and n_perc such that n_harm + n_perc != n_total
    if n_harmonic + n_percussive != n_stems:
        n_harmonic = 0
        n_percussive = 0

    if n_harmonic == 0 and n_percussive == 0: # if default provided, ensuring n_harm and n_perc values are set
        n_harmonic = n_stems // 2
        n_percussive = n_stems - n_harmonic

    json_files = glob.glob(os.path.join(data_home, "*.json"))
    json_percussive = []
    json_harmonic= []

    tempo_bin_harmonic = {}
    tempo_bin_percussive = {}


    for file in json_files: # splitting jsons into harmonic and percussive
        with open(file, "r") as f:
            split_name = os.path.basename(file)
            stem_name, _ = os.path.splitext(split_name)

            data = json.load(f)
            tempo_bin = data.get("tempo bin")
            original_tempo = data.get("tempo")
            instrument_name = data.get("instrument_name")
            key = data.get("key")


            if data.get("sound_class") == "percussive":
                json_percussive.append(file)
                if tempo_bin not in tempo_bin_percussive:
                    tempo_bin_percussive[tempo_bin] = {} # initializing a list for each new tempo bin
                tempo_bin_percussive[tempo_bin][stem_name] = {
                        "original tempo" : original_tempo,
                        "instrument" : instrument_name,
                        "key" : key
                        }


            elif data.get("sound_class") == "harmonic":
                json_harmonic.append(file)
                if tempo_bin not in tempo_bin_harmonic:
                    tempo_bin_harmonic[tempo_bin] = {}
                tempo_bin_harmonic[tempo_bin][stem_name] = {
                        "original tempo" : original_tempo,
                        "instrument" : instrument_name,
                        "key" : key
                        }

                # NEXT STEP IS TO MAKE THIS A DICTIONARY W ALL RELEVANT INFORMATION TO SELECT STEMS

    return n_harmonic, n_percussive, tempo_bin_harmonic, tempo_bin_percussive

def select_tracks(data_home, n_stems, n_harmonic, n_percussive, tempo_bin_harmonic, tempo_bin_percussive, invalid_mixture):

    if invalid_mixture:
        print("invalid")

    try:

        selected_stems = {}

        if n_percussive > 0:
            base_tempo = random.sample(list(tempo_bin_percussive.keys()), 1)[0]

        else:
            base_tempo = random.sample(list(tempo_bin_harmonic.keys()), 1)[0]

        print("base tempo ", base_tempo)

        for i in range(0, n_percussive):

            if tempo_bin_percussive.get(base_tempo) != None:
                percussive_stem = random.sample(list(tempo_bin_percussive.get(base_tempo).keys()), 1)[0]

                instrument = tempo_bin_percussive.get(base_tempo).get(percussive_stem).get("instrument")
                original_tempo = tempo_bin_percussive.get(base_tempo).get(percussive_stem).get("original tempo")
                key = tempo_bin_percussive.get(base_tempo).get(percussive_stem).get("key")

                selected_stems[percussive_stem] = [original_tempo, instrument, key]

            else:
                invalid_mixture = True

        for i in range(0, n_harmonic):

            if tempo_bin_harmonic.get(base_tempo) != None:
                harmonic_stem = random.sample(list(tempo_bin_harmonic.get(base_tempo).keys()), 1)[0]

                instrument = tempo_bin_harmonic.get(base_tempo).get(harmonic_stem).get("instrument")
                original_tempo = tempo_bin_harmonic.get(base_tempo).get(harmonic_stem).get("original tempo")
                key = tempo_bin_harmonic.get(base_tempo).get(harmonic_stem).get("key")

                selected_stems[harmonic_stem] = [original_tempo, instrument, key]

            else:
                invalid_mixture = True

        print("selected stems! ", selected_stems)

        list_of_instruments = []
        for stem in selected_stems.keys():
            instrument = selected_stems.get(stem)[1]
            list_of_instruments.append(instrument)

        # want list of instruments with no None values to make sure no repition where there are instruments filled in
        filtered_instruments = [instr for instr in list_of_instruments if instr is not None]
        if len(filtered_instruments) != len(set(filtered_instruments)): # repeated instrument
            invalid_mixture = True

        if len(selected_stems) != n_stems:
            invalid_mixture = True

    except ValueError as e:
        invalid_mixture = True

    return selected_stems, base_tempo, invalid_mixture


def stretch(data_home, n_stems, selected_stems, base_tempo, invalid_mixture):

    if invalid_mixture:
        print("invalid")

    audio_files = glob.glob(os.path.join(data_home, "*.wav")) + glob.glob(os.path.join(data_home, "*.mp3"))
    stretched_audios = []
    selected_stems_keys = list(selected_stems.keys())

    if invalid_mixture == False:
        target_tempo = base_tempo

        for i in range(0, n_stems):
            stem_to_stretch = selected_stems_keys[i]
            current_tempo = selected_stems[stem_to_stretch][0] # extracting tempo from dict

            for file in audio_files: # is there a way to make this more efficient?
                if stem_to_stretch in file:
                    wav_file = file

            audio, sr = librosa.load(wav_file, sr=DEFAULT_SR)
            audio_norm = librosa.util.normalize(audio)

            audio, sr = librosa.load(wav_file, sr=sr)
            audio_norm = librosa.util.normalize(audio)

            new_rate = float(target_tempo / current_tempo)
            stretched_audio = librosa.effects.time_stretch(audio_norm, rate=new_rate)

    if len(stretched_audios) != n_stems:
        invalid_mixture = True

    return stretched_audios, invalid_mixture

def shift(stretched_audios, invalid_mixture):
    first_downbeats = []
    final_audios = []

    for audio in stretched_audios:
        _, beat_times = librosa.beat.beat_track(y=audio, sr=DEFAULT_SR)
        downbeat_times = librosa.frames_to_time(beat_times, sr=DEFAULT_SR)
        first_downbeats.append(downbeat_times[0])

    latest_beat = max(first_downbeats)
    latest_beat_index = first_downbeats.index(latest_beat)

    immutable_audio = stretched_audios[latest_beat_index]

    final_audios.append(immutable_audio)

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

    return final_audios, invalid_mixture

def generate(data_home, duration, invalid_mixture, stretched_audios):
    if invalid_mixture:
        print("invalid")

    mixture_folder = os.path.join(data_home, "..", "mixtures")
    os.makedirs(mixture_folder, exist_ok = True)

    stretched_audios_lengths = []
    for stem in stretched_audios:
        stretched_audios_lengths.append(len(stem))

    min_length = min(stretched_audios_lengths)
    min_pos = stretched_audios_lengths.index(min_length)

    total_length = min_length

    center = total_length // 2

    start_sample = max(0, total_length - int(duration*DEFAULT_SR))
    end_sample = total_length

    truncated_stems = []
    for audio in stretched_audios:

        audio = audio[:min_length]
        audio = audio[start_sample:end_sample]
        truncated_stems.append(audio)

    length = len(truncated_stems[0])
    mixture_audio = np.zeros(length) # initialization

    for stem in truncated_stems:
        if len(stem) == 0:
            invalid_mixture = True
        mixture_audio += stem

    if invalid_mixture == False: # if it passes all checks

        mixture_id = str(uuid.uuid4())
        individual_output_folder = os.path.join(mixture_folder, mixture_id)
        os.makedirs(individual_output_folder, exist_ok=True)


        for k in range(0, len(truncated_stems)):
            sf.write(f"{individual_output_folder}/stem{k+1}.wav", truncated_stems[k], DEFAULT_SR)


        sf.write(f"{individual_output_folder}/mixture.wav", mixture_audio, DEFAULT_SR)

    return invalid_mixture

def mixture(data_home, n_mixtures, n_stems, n_harmonic, n_percussive, duration):

    n_harmonic, n_percussive, tempo_bin_harmonic, tempo_bin_percussive = precheck(data_home, n_stems, n_harmonic, n_percussive)

    count = 0
    while count < n_mixtures:
        invalid_mixture = False

        selected_stems, base_tempo, invalid_mixture = select_tracks(data_home, n_stems, n_harmonic, n_percussive, tempo_bin_harmonic, tempo_bin_percussive, invalid_mixture)
        if invalid_mixture:
            continue
        stretched_audios, invalid_mixture = stretch(data_home, n_stems, selected_stems, base_tempo, invalid_mixture)
        if invalid_mixture:
            continue
        final_audios, invalid_mixture = shift(stretched_audios, invalid_mixture)
        if invalid_mixture:
            continue

        invalid_mixture = generate(data_home, duration, invalid_mixture, stretched_audios)
        if not invalid_mixture:
            count += 1
