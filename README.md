# stem_mixer
Create coherent mixtures from a folder with any provided stems. The package will infer the needed metadata from the audio files and use it to create mixtures. This package currently only supports .wav audio files.

This package aims to increase the diversity of instruments in mixtures used to train source-separation models.

# Installation

`pip install stem_mixer`

Our library relies on
[python-soundfile](https://python-soundfile.readthedocs.io/en/0.11.0/) for
writing files, which relies on
[libsndfile](http://www.mega-nerd.com/libsndfile/).

# Usage

## Metadata and Feature Extraction
For every stem, we will calculate features and save them on a .json file.

```bash
python script/metadata.py
--data_home=<path_to_stems>
--datasets="brid","musdb"
```

if you want to manually call the `extraction` function to overwrite metadata:

```python
from metadata import extraction

# define the path to your audio stem file
stem_path = "path/to/your/stem/file.wav"

# optionally, provide pre-computed metadata
metadata = {
    "stem_name": stem_name,
    "data_home": data_home,
    "tempo": tempo,
    "key": key,
    "sound_class": sound_class
}

extraction(stem_path, track_metadata=metadata, overwrite=True)
```

to see other variables available, please run

###  Supported Datasets
While we infer features, we support some datasets for which we can infer
features from names information.

- [BRID (Brazilian Rhythmic Instruments Dataset)](https://www.researchgate.net/publication/331589840_A_Novel_Dataset_of_Brazilian_Rhythmic_Instruments_and_Some_Experiments_in_Computational_Rhythm_Analysis)
- [MUSDB18*](https://sigsep.github.io/datasets/musdb.html)

*note: if using MUSDB18, pre-pre-processing step required -->
- must save each stem with "vocals", "drums", "bass", "other" as prefix in .wav filename
- i.e. Detsky Sad - Walkie Talkie - drums.wav
- i.e. Triviul - Angelsaint - vocals.wav
- i.e. PR - Happy Daze - bass.wav
- i.e. Voelund - Comfort Lives In Belief - other.wav


## Mixture Creation


# Tests

first make sure `pytest` is installed:
```bash
pip install pytest
```

if you would like to run our implemented tests of the metadata module, first navigate to your `script` folder and then do the following:

```bash
pytest ../tests/test_md.py
```

If you would like to run our implemented tests of the preprocessing module, first navigate to your `script` folder and then do the following:

```bash
pytest ../tests/test_pre.py
```
