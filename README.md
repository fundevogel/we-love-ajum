# We love AJuM!
[![Release](https://img.shields.io/github/release/Fundevogel/we-love-ajum.svg)](https://github.com/Fundevogel/we-love-ajum/releases) [![License](https://img.shields.io/github/license/Fundevogel/we-love-ajum.svg)](https://github.com/Fundevogel/we-love-ajum/blob/master/LICENSE) [![Issues](https://img.shields.io/github/issues/Fundevogel/we-love-ajum.svg)](https://github.com/Fundevogel/we-love-ajum/issues) [![Status](https://travis-ci.org/fundevogel/we-love-ajum.svg?branch=master)](https://travis-ci.org/fundevogel/we-love-ajum)

This small library is a Python wrapper for [ajum.de](https://www.ajum.de/index.php?s=datenbank), querying the book review database of the working group for children's and youth literature and media ("Arbeitsgemeinschaft Jugendliteratur und Medien", or "AJuM"), which is part of the Education and Science Worker's Union ("Gewerkschaft Erziehung und Wissenschaft", or "GEW").


## Getting started

Running `setup.sh` will install all dependencies inside a virtual environment, ready for action:

```sh
# Set up & activate virtualenv
virtualenv -p python3 venv && source venv/bin/activate

# Install dependencies
python3 -m pip install -r requirements.txt
```


## Usage

For convenience, there are four basic commands available:

```text
$ doit list
backup_db     Backs up remote database
build_db      Builds local database
build_index   Builds index of reviews per ISBN
clear_cache   Removes cached index files
```

For everything else, check out `src/ajum.py` - feedback appreciated, as always!

**Note:** As you can see, `index.json` (which is included in this repository) contains references for all ISBNs being reviewed, with a total of 8766 currently available reviews - so if you need reviews for a known ISBN, check it out & visit `https://www.ajum.de/index.php?s=datenbank&id=YOUR_ID` or get your hands dirty like so:

```python
from src.ajum import Ajum

# Create object
obj = Ajum()

# Fetch review data
data = obj.fetch_review('YOUR_ID')
```


# Disclaimer

For legal reasons (see [here](https://www.ajum.de/html/nutzungserlaubnis_f_rezensionen.pdf)) we only provide you with the means to download reviews. We assume neither ownership nor intellectual property of any review - which are publically available on the AJuM website and are subject to their legal sphere alone.

**Happy coding!**


:copyright: Fundevogel Kinder- und Jugendbuchhandlung
