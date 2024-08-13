from stem_mixer.metadata import process
from stem_mixer.mix import generate_mixtures

data_home = "../../stems"
datasets = ["brid", "musdb"]

# generate metadata
process(data_home, datasets)

# generate mixtures
n_mixtures = 3
n_stems = 2
n_percussive = 1
n_harmonic = 1
duration = 10

generate_mixtures(data_home, n_mixtures, n_stems, n_percussive, n_harmonic,
        duration)
