# stem_mixer
this package will take a folder of stems and create coherent mixtures of desired length and number of stems (defaults will be provided if not given). the user can also declare a harmonic-to-percussive ratio they would like the mixtures to follow (again, defaults will be provided if not given). an output folder will be created where the mixtures will be stored as folders themselves in which the final audio file and its respective stem audio files will go. when working with BRID and MUSDB datasets, the user can opt to use included pre-processing for those datasets to increase coherency of results. the user could also manually provide metadata about the stems they are using which could increase coherency of results. however, the package is designed to generate coherent mixtures even when no initial metadata is given as a pre-processing step. the goal is that this package can help increase the diversity of mixture / stem data being used to train source-separation models. 

# example usage // without dataset-specific pre-processing
if you want to generate mixtures, you do the following

```bash
python script/main.py
--data_home=<path_to_folder>
```

to see other variables available, please run

`python script/main.py --help`

# example usage // dataset-specific pre-processing 
SUPPORTED DATASETS:
- BRID (Brazilian Rhythmic Instruments Dataset)
- MUSDB18* 

*note: if using MUSDB18, pre-pre-processing step required --> 
- must save each stem with "vocals", "drums", "bass", "other" in .wav filename 

if you want to generate mixtures using supported datasets, you do the following

```bash
python script/preprocessing.py
--data_home=<path_to_folder>
--dataset=<"brid" or "musdb">
```

to see other variables available, please run

`python script/preprocessing.py --help`

# Folder structure
We expect the following folder structure:

- data_home
    - stems
