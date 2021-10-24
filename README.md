# We love AJuM!
[![Release](https://img.shields.io/github/release/Fundevogel/we-love-ajum.svg)](https://github.com/Fundevogel/we-love-ajum/releases) [![License](https://img.shields.io/github/license/Fundevogel/we-love-ajum.svg)](https://github.com/Fundevogel/we-love-ajum/blob/master/LICENSE) [![Issues](https://img.shields.io/github/issues/Fundevogel/we-love-ajum.svg)](https://github.com/Fundevogel/we-love-ajum/issues) [![Status](https://travis-ci.org/fundevogel/we-love-ajum.svg?branch=master)](https://travis-ci.org/fundevogel/we-love-ajum)

This small library is a Python wrapper for [ajum.de](https://www.ajum.de/index.php?s=datenbank), querying the book review database of the german working group for children's and youth literature and media ("Arbeitsgemeinschaft Jugendliteratur und Medien" or "AJuM"), which is part of the german Education and Science Worker's Union ("Gewerkschaft Erziehung und Wissenschaft" or "GEW").

We deem their work to be invaluable for kindergartens, (pre)schools, universities and other educational institutions. We are thankful for AJuM's commitment and want to give something back by spreading the word and provide an easy way to interact with their review database.

**Note:** We DO NOT want to disrupt their services in any way, so by default the responsible function `sleep()`s for three seconds after each API call. Furthermore, as downloading reviews *just* to build an index file means making A LOT of requests, we included `index.json`. It was created using `strict` mode (which means that invalid ISBNs were skipped) and contains all review IDs per ISBN - currently totalling 44757 (valid) ISBNs with 83710 reviews (averaging 1.87 reviews per ISBN).


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

From there, it's easy to roll out your own script:

```python
from src.ajum import Ajum

# Initialize object
ajum = Ajum()

# Fetch review data
data = ajum.get_review('SOME_ID')
```

For more examples, have a look at `src/cli.py` and `src/ajum.py` to get you started - feedback appreciated, as always!


## Usage

The following commands are available:

```text
$ ajum --help
Usage: ajum [OPTIONS] COMMAND [ARGS]...

  Tools for interacting with the 'AJuM' database.

Options:
  -t, --timer FLOAT      Waiting time after each request.
  -f, --is_from TEXT     "From" header.
  -u, --user-agent TEXT  User agent.
  -v, --verbose          Enable verbose mode.
  --version              Show the version and exit.
  --help                 Show this message and exit.

Commands:
  backup  Backs up remote database
  build   Builds local database DB_FILE from INDEX_FILE
  clear   Removes cached results files
  index   Exports index of reviews per ISBN to INDEX_FILE
  query   Queries remote database
  show    Shows data of given REVIEW
  stats   Shows statistics
  update  Updates local database
```


## Commands

### `backup`

.. remote database:

```text
$ ajum backup --help
Usage: ajum backup [OPTIONS]

  Backs up remote database

Options:
  -a, --archived        Include all reviews.
  -h, --html-file PATH  HTML results file.
  --help                Show this message and exit.
```


### `index`

.. reviews per ISBN:

```text
$ ajum index --help
Usage: ajum index [OPTIONS] [INDEX_FILE]

  Exports index of reviews per ISBN to INDEX_FILE

Options:
  -s, --strict        Whether to skip invalid ISBNs.
  -j, --jobs INTEGER  Number of threads.
  --help              Show this message and exit.
```


### `build`

.. local database:

```text
$ ajum build --help
Usage: ajum build [OPTIONS] [INDEX_FILE] [DB_FILE]

  Builds local database DB_FILE from INDEX_FILE

Options:
  -j, --jobs INTEGER  Number of threads.
  --help              Show this message and exit.
```


### `show`

.. review data for given ID:

```text
$ ajum show --help
Usage: ajum show [OPTIONS] REVIEW

  Shows data of given REVIEW

Options:
  --help  Show this message and exit.
```


### `query`

.. remote database for given search terms:

```text
$ ajum query --help
Usage: ajum query [OPTIONS]

  Queries remote database

Options:
  -s, --search-term TEXT  Search term.
  -t, --title TEXT        Book title.
  -f, --first-name TEXT   First name of author.
  -l, --last-name TEXT    Last name of author.
  -i, --illustrator TEXT  Name of illustrator.
  -a, --all-reviews       Include all reviews.
  -w, --wolgast           Include only Wolgast laureates.
  --help                  Show this message and exit.
```


### `clear`

.. cached results files:

```text
$ ajum clear --help
Usage: ajum clear [OPTIONS]

  Removes cached results files

Options:
  --help  Show this message and exit.
```


# Disclaimer

For legal reasons (see [here](https://www.ajum.de/html/nutzungserlaubnis_f_rezensionen.pdf)) we only provide you with the means to download reviews. We assume neither ownership nor intellectual property of any review - they are publically available on the AJuM website and are subject to their legal sphere alone.

**Happy coding!**


:copyright: Fundevogel Kinder- und Jugendbuchhandlung
