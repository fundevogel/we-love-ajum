import os
import re
import glob
import statistics
import multiprocessing

import click
import isbnlib

from .ajum import Ajum
from .helpers import dump_json, load_json


@click.group()
@click.pass_context
@click.option('-t', '--timer', default=5.0, type=float, help='Waiting time after each request.')
@click.option('-f', '--is_from', help='"From" header.')
@click.option('-u', '--user-agent', help='User agent.')
@click.option('-v', '--verbose', count=True, help='Enable verbose mode.')
@click.version_option('0.7.3')
def cli(ctx, timer: float, is_from: str, user_agent: str, verbose: int) -> None:
    """
    Tools for interacting with the 'AJuM' database.
    """

    # Ensure context object exists & is dictionary
    ctx.ensure_object(dict)

    # Initialize context object
    # (1) Defaults
    ctx.obj = {
        'cache_dir': click.get_app_dir('ajum'),
        'timer': timer,
    }

    # (2) 'From' header
    if is_from:
        ctx.obj['is_from'] = is_from

    # (3) User agent
    if user_agent:
        ctx.obj['user_agent'] = user_agent

    # Assign verbose mode
    ctx.obj['verbose'] = verbose


@cli.command()
@click.pass_context
@click.option('-a', '--archived', is_flag=True, help='Include all reviews.')
@click.option('-h', '--html-file', type=click.Path(True), help='HTML results file.')
def backup(ctx, archived: bool, html_file) -> None:
    """
    Backs up remote database
    """

    # Initialize object
    ajum = init(ctx.obj)

    # If HTML results page is provided ..
    if html_file:
        if ctx.obj['verbose'] > 1: click.echo('HTML file found: {} ..'.format(html_file))

        # .. check if it was loaded before
        json_file = os.path.join(ajum.cache_dir, html_file.replace('.html', '.json'))

        # If not ..
        if not os.path.exists(json_file):
            if ctx.obj['verbose'] > 1: click.echo('No JSON found: {} ..'.format(json_file))

            # (1) .. load its contents
            with open(html_file, 'r') as file:
                html = file.read()

            # (2) .. extract review IDs & store them
            dump_json(ajum.extract_results(html), json_file)

        reviews = load_json(json_file)

    # .. otherwise ..
    else:
        if ctx.obj['verbose'] > 1: click.echo('Fetching review IDs from remote database ..')

        # .. make requests to get them
        reviews = ajum.get_results({
            'start': '0',
            'do': 'suchen',
            'bewertung': '0',
            'einsatz': '0',
            'medienart': '0',
            'alter': '0',
            'gattung': '0',
            'archiv': 'JA' if archived else '',
        })

    # Loop over review IDs
    for review in set(reviews):
        # Check if review was cached before
        html_file = ajum.id2file(review)

        if not re.match(r'\d+', review):
            # .. report it
            click.echo('Invalid review ID "{}", exiting ..'.format(review))

            # .. exit
            click.Context.abort()

        # If not ..
        if not os.path.exists(html_file):
            # (1) .. report it
            if ctx.obj['verbose'] > 0: click.echo('Fetching {} ..'.format(html_file))

            # (2) .. cache it
            ajum.fetch_review(review)


@cli.command()
@click.pass_context
@click.option('-l', '--limit', default=50, type=int, help='Limit of reviews.')
def update(ctx, limit: int) -> None:
    """
    Updates local database
    """

    # Initialize object
    ajum = init(ctx.obj)

    if ctx.obj['verbose'] > 1: click.echo('Fetching review IDs from remote database ..')

    # Make requests to get reviews from results pages
    # TODO: Since 'limit' shows ALL results on EVERY results page (strangely up to 12526),
    # this could be done in one request, but this would easily mislead people to increase
    # limits until reaching the server's maximum RAM so it's discouraged
    reviews = ajum.get_results({
        'do': 'suchen',
        'start': '0',
        'show': 'last',
        'limit': limit,
    })

    # Loop over review IDs
    for review in set(reviews):
        # Check if review was cached before
        html_file = ajum.id2file(review)

        if not re.match(r'\d+', review):
            # .. report it
            click.echo('Invalid review ID "{}", exiting ..'.format(review))

        # If not ..
        if not os.path.exists(html_file):
            # (1) .. report it
            if ctx.obj['verbose'] > 0: click.echo('Fetching {} ..'.format(html_file))

            # (2) .. cache it
            ajum.fetch_review(review)


@cli.command()
@click.pass_context
@click.argument('index-file', default='index.json', type=click.Path(False))
@click.option('-s', '--strict', is_flag=True, help='Whether to skip invalid ISBNs.')
@click.option('-j', '--jobs', default=4, type=int, help='Number of threads.')
def index(ctx, index_file: str, strict: bool, jobs: int) -> None:
    """
    Exports index of reviews per ISBN to INDEX_FILE
    """

    # Initialize object
    ajum = init(ctx.obj)

    # Implement global indexing method
    global add2index

    def add2index(html_file, index, lock):
        # Get review ID from filename
        review = ajum.file2id(html_file)

        # Load review data
        data = ajum.get_review(review)

        # If field 'ISBN' is empty ..
        if 'ISBN' not in data:
            # .. we got a problem
            return

        # Assign reviewed ISBN
        isbn = data['ISBN']

        # If 'strict' mode is enabled ..
        if strict:
            # (1) .. check if ISBN valid ..
            if isbnlib.notisbn(isbn):
                if ctx.obj['verbose'] > 0: click.echo('Skipping invalid ISBN {} ..'.format(isbn))

                # .. otherwise skip it
                return

            # (2) .. ensure hyphenated notation
            # See https://github.com/xlcnd/isbnlib/issues/86
            if isbnlib.mask(isbn):
                isbn = isbnlib.mask(isbn)

        if ctx.obj['verbose'] > 0: click.echo('Adding review for {} ..'.format(isbn))

        # Acquire lock
        lock.acquire()

        # Create record (if not present)
        if isbn not in index:
            index[isbn] = []

        # Add review to ISBN
        # See https://stackoverflow.com/a/8644552
        buffer = index[isbn]
        buffer.append(review)
        index[isbn] = buffer

        # Release lock
        lock.release()

    # Create process pool
    pool = multiprocessing.Pool(jobs)

    # Initialize manager object
    manager = multiprocessing.Manager()

    # Prepare index storage
    isbns = manager.dict()

    # Create lock
    lock = manager.Lock()

    # Iterate over cached reviews ..
    for html_file in glob.glob(ajum.cache_dir + '/*.html'):
        # .. retrieving data using multiple processes
        pool.apply_async(add2index, args=(html_file, isbns, lock))

    # Combine results
    pool.close()
    pool.join()

    if ctx.obj['verbose'] > 1: click.echo('Creating index file {} ..'.format(index_file))

    # Create index file
    dump_json(dict(sorted(isbns.items())), index_file)


@cli.command()
@click.argument('index-file', default='index.json', type=click.Path(True))
@click.argument('db-file', default='database.json', type=click.Path(False))
@click.option('-j', '--jobs', default=4, type=int, help='Number of threads.')
@click.pass_context
def build(ctx, index_file: str, db_file: str, jobs: int) -> None:
    """
    Builds local database DB_FILE from INDEX_FILE
    """

    # Initialize object
    ajum = init(ctx.obj)

    # Implement global indexing method
    global add2database

    def add2database(isbn, reviews, data):
        # Create data buffer
        buffer = {}

        if ctx.obj['verbose'] > 0: click.echo('Adding reviews for {} ..'.format(isbn))

        for review in reviews:
            # Define HTML file for review page
            html_file = ajum.id2file(review)

            # If not cached (anymore) ..
            if not os.path.exists(html_file):
                # .. skip it
                continue

            # Load review HTML
            with open(html_file, 'r') as file:
                html = file.read()

            # Extract data & store it
            buffer[review] = ajum.extract_review(html)

        # Add reviews to data
        data[isbn] = buffer

    # Initialize manager object
    manager = multiprocessing.Manager()

    # Prepare database storage
    isbns = manager.dict()

    # Create process pool
    pool = multiprocessing.Pool(jobs)

    # Iterate over indexed ISBNs ..
    for isbn, reviews in load_json(index_file).items():
        # .. retrieving data using multiple processes
        pool.apply_async(add2database, args=(isbn, reviews, isbns))

    # Combine results
    pool.close()
    pool.join()

    if ctx.obj['verbose'] > 1: click.echo('Creating database file {} ..'.format(db_file))

    # Create database file
    dump_json(dict(sorted(isbns.items())), db_file)


@cli.command()
@click.pass_context
@click.argument('review')
def show(ctx, review: str) -> None:
    """
    Shows data of given REVIEW
    """

    # Initialize object
    ajum = init(ctx.obj)

    # Fetch review
    data = ajum.get_review(review)

    # If review exists ..
    if data:
        # .. print its data
        for key, value in data.items():
            click.echo('{}: {}'.format(key, value))

    else:
        click.echo('No review found for given ID, please try again.')


@cli.command()
@click.pass_context
@click.option('-s', '--search-term', default='', help='Search term.')
@click.option('-t', '--title', default='', help='Book title.')
@click.option('-f', '--first-name', default='', help='First name of author.')
@click.option('-l', '--last-name', default='', help='Last name of author.')
@click.option('-i', '--illustrator', default='', help='Name of illustrator.')
@click.option('-a', '--all-reviews', is_flag=True, help='Include all reviews.')
@click.option('-w', '--wolgast', is_flag=True, help='Include only Wolgast laureates.')
def query(ctx, search_term: str, title: str, first_name: str, last_name: str, illustrator: str, all_reviews: bool, wolgast: bool) -> None:
    """
    Queries remote database
    """

    # Initialize object
    ajum = init(ctx.obj)

    # Query database
    reviews = ajum.query(
        search_term=search_term,
        title=title,
        first_name=first_name,
        last_name=last_name,
        illustrator=illustrator,
        archive=all_reviews,
        wolgast=wolgast
    )

    if reviews:
        # Count reviews
        count = len(reviews)

        click.echo('We found {} reviews.'.format(count))

        # If confirmed ..
        if click.confirm('Show results?'):
            # .. loop over reviews ..
            for i, review in enumerate(reviews):
                # Increase by one for human-readable numbering
                i += 1

                # Let user know where we are
                click.echo('Review {} of {}:'.format(str(i), count))

                # Print review data
                for key, value in ajum.get_review(review).items():
                    click.echo('{}: {}'.format(key, value))

                # Add newline for improved spacing
                click.echo('\n')

                # Exit script upon last entry
                if i == count:
                    click.echo('No more entries, exiting ..')

                    # Goodbye!
                    break

                # Always remember this: If told to ..
                if not click.confirm('Continue?'):
                    # .. stop!
                    break

    else:
        click.echo('Your query did not match any review, please try again.')


@cli.command()
@click.pass_context
def clear(ctx) -> None:
    """
    Removes cached results files
    """

    # Initialize object
    ajum = init(ctx.obj)

    if ctx.obj['verbose'] > 1: click.echo('Flushing cache ..')

    # Flush cache
    ajum.clear_cache()


@cli.command()
@click.pass_context
@click.option('-i', '--index-file', default='index.json', type=click.Path(False), help='Index file.')
def stats(ctx, index_file: str) -> None:
    """
    Shows statistics
    """

    # Initialize object
    ajum = init(ctx.obj)

    # Count cached reviews
    review_count = len(glob.glob(ajum.cache_dir + '/*.html'))

    # Report it
    click.echo('There are currently ..')
    click.echo('.. {} reviews in cache.'.format(review_count))

    # If index file exists ..
    if os.path.exists(index_file):
        # .. count indexed ISBNs & reviews
        index = load_json(index_file)
        index_count = len(index.keys())
        review_count = sum([len(item) for item in index.values()])

        # Report it
        click.echo('.. {} reviews indexed.'.format(review_count))
        click.echo('.. {} ISBNs indexed.'.format(index_count))

        # Report average & median reviews per ISBN
        average = review_count / index_count
        median = int(statistics.median(sorted([len(value) for value in index.values()])))

        click.echo('--')
        click.echo('Reviews per ISBN ..')
        click.echo('.. median of {}'.format(median))
        click.echo('.. averaging {:.2f}'.format(average))


def init(obj) -> Ajum:
    """
    Initializes "AJuM" instance from given context object
    """

    # Initialize object
    ajum = Ajum()

    # Configure options
    # (1) Cache directory
    ajum.cache_dir = obj['cache_dir']

    # (2) Waiting time after each request
    ajum.timer = obj['timer']

    # (3) 'From' header
    if 'is_from' in obj:
        ajum.headers['From'] = obj['is_from']

    # (4) User agent
    if 'user_agent' in obj:
        ajum.headers['User-Agent'] = obj['user_agent']

    return ajum
