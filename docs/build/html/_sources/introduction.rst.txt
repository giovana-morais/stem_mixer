Introduction
============

``stem_mixer`` is a tool designed to generate coherent mixtures from a set of provided stems in order to provide accessible and diverse training data 
for source separation models.

Key Features
------------

- **Preprocessing**: Extracts essential metadata from each stem by cross-referencing with known metadata from supported datasets or inferring such values.
- **Mix**: Selects stems based on tempo proximity to stretch and align them. User can indicate desired duration, harmonic-to-percussive ratio, number of stems, and number of mixtures.