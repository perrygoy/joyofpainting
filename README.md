# Joy of Painting
This is my implementation of the Joy of Painting code challenge at The Nerdery, using a genetic algorithm!

## Summary of Requirements
Recreate famous paintings by Bob Ross and other artists! Painting recreations can only have 500 strokes, and are scored based on pixel-by-pixel similarity to the original work.

# Getting Started
 * Copy `secrets.skel` to `secrets.py` and fill in the missing values.
 * Download the [Local Testing Tools](http://joyofpainting.nerderylabs.com/localTesting) (the instructions are also on that site).
 * Create a Python 3 virtual environment: `python3 -m venv env`
 * Activate your venv: `source env/bin/activate`
 * Install dependencies: `pip install -r requirements.txt`
 * Download the images you want to recreate, name them `<number>.png`, and put them into `images/reference/` (e.g. `images/reference/1.png`, `images/reference/2.png`, etc.)
 * Run the script! `python jop.py --help`
