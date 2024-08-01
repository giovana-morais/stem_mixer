# stem_mixer
this package will take a folder of stems and create coherent mixtures of desired length and stem count (defaults will be provided if not given). the user can also declare a harmonic-to-percussive ratio they would like the mixtures to follow (again, defaults will be provided if not given). an output folder will be created where the mixtures will be stored as folders themselves in which the final audio file and its respective stem audio files will go. metadata will be inferred for each stem or assigned if stem matches into a supported dataset. the user could also manually provide metadata about the stems they are using which could increase coherency of results if they are certain about specific attributes. however, the package is designed to generate coherent mixtures even when no initial metadata is given as a pre-processing step. the goal is that this package can help increase the diversity of mixture / stem data being used to train source-separation models and allow for data mobility outside of traditional, western datasets. 

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

# folder structure
we expect the following folder structure:

- data_home
    - example_stem1.wav
    - example_stem1.json
    - example_stem2.wav
    - example_stem2.json
      ...
