import os
import re
import glob

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
@click.version_option('0.6.0')
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
@click.option('-f', '--force', is_flag=True, help='Force cache reload.')
@click.option('-a', '--archived', is_flag=True, help='Include all reviews.')
@click.option('-h', '--html-file', type=click.Path(True), help='Results page as HTML file.')
def backup(ctx, force: bool, archived: bool, html_file) -> None:
    """
    Backs up remote database
    """

    if ctx.obj['verbose'] > 1: click.echo('Initializing "AJuM" instance ..')

    # Initialize object
    ajum = init(ctx.obj)

    # If 'force' mode is activated ..
    if force:
        if ctx.obj['verbose'] > 1: click.echo('Clearing cache ..')

        # .. clear exisiting cache first
        ajum.clear_cache()

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
            'archiv': 'JA' if archived else '',
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
@click.option('-f', '--force', is_flag=True, help='Force cache reload.')
@click.option('-l', '--limit', default=50, type=int, help='Limit of reviews.')
def update(ctx, force: bool) -> None:
    """
    Updates local database
    """

    if ctx.obj['verbose'] > 1: click.echo('Initializing "AJuM" instance ..')

    # Initialize object
    ajum = init(ctx.obj)

    # If 'force' mode is activated ..
    if force:
        if ctx.obj['verbose'] > 1: click.echo('Clearing cache ..')

        # .. clear exisiting cache first
        ajum.clear_cache()

    if ctx.obj['verbose'] > 1: click.echo('Fetching review IDs from remote database ..')

    # .. make requests to get them
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
def index(ctx, index_file: str, strict: bool) -> None:
    """
    Exports index of reviews per ISBN to INDEX_FILE
    """

    if ctx.obj['verbose'] > 1: click.echo('Initializing "AJuM" instance ..')

    # Initialize object
    ajum = init(ctx.obj)

    # Prepare index storage
    index = {}

    for html_file in glob.glob(ajum.cache_dir + '/*.html'):
        # Get review ID from filename
        review = ajum.file2id(html_file)

        # Load review data
        data = ajum.get_review(review)

        # If field 'ISBN' is empty ..
        if 'ISBN' not in data:
            # .. we got a problem
            continue

        # Assign reviewed ISBN
        isbn = data['ISBN']

        # If 'strict' mode is enabled ..
        if strict:
            # (1) .. check if ISBN valid ..
            if isbnlib.notisbn(isbn):
                if ctx.obj['verbose'] > 0: click.echo('Skipping invalid ISBN {} ..'.format(isbn))

                # .. otherwise skip it
                continue

            # (2) .. ensure hyphenated notation
            # See https://github.com/xlcnd/isbnlib/issues/86
            if isbnlib.mask(isbn):
                isbn = isbnlib.mask(isbn)

        if ctx.obj['verbose'] > 0: click.echo('Adding review for {} ..'.format(isbn))

        # Create record (if not present)
        if isbn not in index:
            index[isbn] = []

        # Add review to ISBN
        index[isbn].append(review)

    if ctx.obj['verbose'] > 1: click.echo('Creating index file {} ..'.format(index_file))

    # Create index file
    dump_json(dict(sorted(index.items())), index_file)


@cli.command()
@click.argument('index-file', default='index.json', type=click.Path(True))
@click.argument('db-file', default='database.json', type=click.Path(False))
@click.pass_context
def build(ctx, index_file: str, db_file: str) -> None:
    """
    Builds local database DB_FILE from INDEX_FILE
    """

    if ctx.obj['verbose'] > 1: click.echo('Initializing "AJuM" instance ..')

    # Initialize object
    ajum = init(ctx.obj)

    # Prepare database store
    data = {}

    for isbn, reviews in load_json(index_file).items():
        # Create record
        data[isbn] = {}

        for review in reviews:
            # Define HTML file for review page
            html_file = ajum.id2file(review)

            # If not cached yet ..
            if not os.path.exists(html_file):
                # .. we got a problem
                continue

            # Load review HTML
            with open(html_file, 'r') as file:
                html = file.read()

            # Extract data & store it
            data[isbn][review] = ajum.extract_review(html)

    if ctx.obj['verbose'] > 1: click.echo('Creating database file {} ..'.format(db_file))

    # Create database file
    dump_json(data, db_file)


@cli.command()
@click.pass_context
def clear(ctx) -> None:
    """
    Removes cached files
    """

    # Initialize object
    ajum = init(ctx.obj)

    if ctx.obj['verbose'] > 1: click.echo('Flushing cache ..')

    # Flush cache
    ajum.clear_cache()


@cli.command()
@click.pass_context
@click.argument('review')
def show(ctx, review: str) -> None:
    """
    Shows data of given REVIEW
    """

    if ctx.obj['verbose'] > 1: click.echo('Initializing "AJuM" instance ..')

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
@click.option('-s', '--search-term', default='', help='Force cache reload.')
@click.option('-t', '--title', default='', help='Include all reviews.')
@click.option('-f', '--first-name', default='', help='Include all reviews.')
@click.option('-l', '--last-name', default='', help='Include all reviews.')
@click.option('-l', '--last-name', default='', help='Include all reviews.')
@click.option('-i', '--illustrator', default='', help='Include all reviews.')
@click.option('-a', '--all-reviews', is_flag=True, help='Include all reviews.')
@click.option('-w', '--wolgast', is_flag=True, help='Include all reviews.')
def query(ctx, search_term: str, title: str, first_name: str, last_name: str, illustrator: str, all_reviews: bool, wolgast: bool) -> None:
    """
    Queries remote database
    """

    if ctx.obj['verbose'] > 1: click.echo('Initializing "AJuM" instance ..')

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
    click.echo('Currently {} reviews in cache.'.format(review_count))

    # If index file exists ..
    if os.path.exists(index_file):
        # .. count ISBNs
        index = load_json(index_file)
        index_count = len(index.keys())

        # Report it
        click.echo('Currently {} ISBNs indexed.'.format(index_count))

        # Import 'statistics' library
        import statistics

        # Report average & median reviews per ISBN
        average = review_count / index_count
        median = int(statistics.median(sorted([len(value) for value in index.values()])))

        click.echo('.. averaging {:.2f} reviews per ISBN & a median of {}.'.format(average, median))
