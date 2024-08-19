import glob
import os

import loopextractor
import tqdm


stem_folder = "/home/gigibs/Documents/stems"
output_path = "/home/gigibs/Documents/stems/loops"

wav_files = glob.glob(os.path.join(stem_folder, "*.wav"))
mp3_files = glob.glob(os.path.join(stem_folder, "*.mp3"))

audio_files = wav_files + mp3_files

os.makedirs(output_path, exist_ok=True)

error_tracks = []

for audio in tqdm.tqdm(audio_files):
    # loopextractor.run_algorithm(audio, n_templates=[30,25,10], output_savename=os.path.join(output_path, audio))
    out_name = os.path.join(output_path, os.path.basename(audio))
    try:
        loopextractor.run_algorithm(audio, n_templates=[0,0,0],
                output_savename=out_name)
    except:
        error_tracks.append(audio)
        print(f"error processing {os.path.basename(audio)}. moving on")

print(f"unable to process the following tracks: {error_tracks}")
