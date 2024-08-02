from setuptools import setup, find_packages

if __name__ == "__main__":
	setup(
	    name="stem_mixer",
	    version="0.1.0",
	    description="data generation for training source separation models",
	    packages=find_packages(),
	    install_requires=[
	        "numpy>=1.26.4",
	        "librosa>=0.10.2.post1",
	        "soundfile>=0.12.1",
	        "tqdm>=4.66.4"

	    ],
	    author="Giovana Morais and Lindsey Pietrewicz",
	    author_email="lgp3212@nyu.edu",
	    url="https://github.com/giovana-morais/stem_mixer",
	    classifiers=[
	        "Programming Language :: Python :: 3"
	    ],
	    python_requires=">=3.10.12",
	)