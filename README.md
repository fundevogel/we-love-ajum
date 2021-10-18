# We love AJuM!
[![Release](https://img.shields.io/github/release/Fundevogel/we-love-ajum.svg)](https://github.com/Fundevogel/we-love-ajum/releases) [![License](https://img.shields.io/github/license/Fundevogel/we-love-ajum.svg)](https://github.com/Fundevogel/we-love-ajum/blob/master/LICENSE) [![Issues](https://img.shields.io/github/issues/Fundevogel/we-love-ajum.svg)](https://github.com/Fundevogel/we-love-ajum/issues) [![Status](https://travis-ci.org/fundevogel/we-love-ajum.svg?branch=master)](https://travis-ci.org/fundevogel/we-love-ajum)

This small library is a Python wrapper for [ajum.de](https://www.ajum.de/index.php?s=datenbank), querying the book review database of the german working group for children's and youth literature and media ("Arbeitsgemeinschaft Jugendliteratur und Medien" or "AJuM"), which is part of the german Education and Science Worker's Union ("Gewerkschaft Erziehung und Wissenschaft" or "GEW").

We deem their work to be invaluable for kindergartens, (pre)schools, universities and other educational institutions. We are thankful for AJuM's commitment and want to give something back by spreading the word and provide an easy way to interact with their review database.

**Note:** We DO NOT want to disrupt their services in any way, so by default the responsible function `sleep()`s for three seconds after each API call.


## Getting started

Running `setup.bash` will install all dependencies inside a virtual environment, ready for action:

```bash
# Set up & activate virtualenv
virtualenv -p python3 venv

# shellcheck disable=SC1091
source venv/bin/activate

# Install dependencies
python -m pip install --editable .
```


## Usage

The following commands are available:

```text
$ ajum --help
Usage: ajum [OPTIONS] COMMAND [ARGS]...

  Tools for interacting with the 'AJuM' database.

Options:
  --version              Show the version and exit.
  -i, --index-file PATH  Index file.
  -d, --db-file PATH     Database file.
  -c, --cache-dir PATH   Cache directory.
  -t, --timer FLOAT      Waiting time after each request.
  -f, --is_from TEXT     "From" header.
  -u, --user-agent TEXT  User agent.
  --help                 Show this message and exit.

Commands:
  backup  Backs up remote database
  build   Builds local database
  clear   Removes cached files
  index   Indexes reviews per ISBN
  query   Queries remote database
  show    Shows data of given REVIEW
```

For everything else, check out the `--help` command, like this: `ajum backup --help` .. or have a look at `src/ajum.py` - feedback appreciated, as always!

**Note:** As downloading reviews *just* to build an index file means making A LOT of requests, we included `index.json`, which contains references for all ISBNs being reviewed, with a total of 8766 currently available reviews - so if you need reviews for a known ISBN, get *only* what you need simply like so:

```bash
$ ajum show YOUR_ID
```

.. or get your hands dirty and start your own script:

```python
from src.ajum import Ajum

# Initialize object
ajum = Ajum()

# Fetch review data
data = ajum.get_review('YOUR_ID')
```

.. or visit `https://www.ajum.de/index.php?s=datenbank&id=YOUR_ID` - nah, just kidding :)


# Disclaimer

For legal reasons (see [here](https://www.ajum.de/html/nutzungserlaubnis_f_rezensionen.pdf)) we only provide you with the means to download reviews. We assume neither ownership nor intellectual property of any review - they are publically available on the AJuM website and are subject to their legal sphere alone.

**Happy coding!**


:copyright: Fundevogel Kinder- und Jugendbuchhandlung
