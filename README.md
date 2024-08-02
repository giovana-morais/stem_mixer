# stem_mixer
Create coherent mixtures from a folder with stems you have. The package will infer the needed metadata from the audio files and use it to create mixtures.

This package aims to increase the diversity of instruments in mixtures used to train source-separation models.

# example usage - metadata creation

SUPPORTED DATASETS FOR NON-INFERRAL METADATA CREATION:
- BRID (Brazilian Rhythmic Instruments Dataset)
- MUSDB18* 

*note: if using MUSDB18, pre-pre-processing step required --> 
- must save each stem with "vocals", "drums", "bass", "other" as prefix in .wav filename
- i.e. Detsky Sad - Walkie Talkie - drums.wav
- i.e. Triviul - Angelsaint - vocals.wav
- i.e. PR - Happy Daze - bass.wav
- i.e. Voelund - Comfort Lives In Belief - other.wav

WHEN DATA IS INCLUDED FROM OTHER DATASETS OR SOURCES, METADATA VALUES WILL BE INFERRED

if you want to pre-process data for mixing (create json files with essential metadata), you do the following
```bash
python script/preprocessing.py
--data_home=<path_to_stems>
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

`python script/main.py --help`

# example usage - mixture creation

if you want to generate mixtures using supported datasets, you do the following

```bash
python script/main.py
--data_home=<path_to_stems>
```

to see other variables available, please run

`python script/main.py --help`

# example usage - tests

first make sure `pytest` is installed:
```bash
pip install pytest
```

if you would like to run our implemented tests of the metadata module, first navigate to your `script` folder and then do the following:

```bash
pytest ../tests/test_md.py
```

if you would like to run our implemented tests of the preprocessing module, first navigate to your `script` folder and then do the following:

```bash
pytest ../tests/test_pre.py
```

# folder structure
we expect the following folder structure:

- data_home
    - example_stem1.wav
    - example_stem1.json
    - example_stem2.wav
    - example_stem2.json
      ...
