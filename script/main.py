import argparse
import os

import metadata
import mix


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog="StemMixer",
            description="Generating mixtures"
            )
    parser.add_argument("--data_home", required=True, help="pathway to where is data is stored")

    parser.add_argument("--duration", type=float, default=5.0, required=False, help="set mixture duration. default is 5 seconds")

    parser.add_argument("--n_mixtures", required=False, default=5, help="number of mixtures created")
    parser.add_argument("--n_stems", required=False, default=3, help="number of stems pertaining to each mix")
    parser.add_argument("--n_harmonic", required=False, default=0, help="number of harmonic stems")
    parser.add_argument("--n_percussive", required=False, default=0, help="number of percussive stems")

    args = parser.parse_args()
    kwargs = vars(args)

    mix.mixture(args.data_home, args.n_mixtures, args.n_stems, args.n_harmonic, args.n_percussive)

